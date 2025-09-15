#!/usr/bin/env python3
"""
CDX Export (JSONL): CC-MAIN-2025-30, latest per digest, HTTP 200, HTML only.
- Auto-creates domains_csv (single column 'domain') from config['domains_location']
- Creates domains_norm view (lowercase + strip leading 'www.')
- Adds just the target crawl/subset partition
- Verifies via ccindex$partitions (no data scan)
- Exports newline-delimited JSON (gz) using json_format(map(...))
"""

import sys
import os
import json
import time
from dotenv import load_dotenv

# Allow local package imports like src.aws.athena_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.aws.athena_client import AthenaClient  # noqa: E402


def main():
    crawl_id = "CC-MAIN-2025-30"
    subset = "warc"

    print("📋 Common Crawl CDX Export — Latest per Digest, 200, HTML")
    print("=" * 80)

    # Load config
    with open("src/config/aws_config.json", "r") as f:
        config = json.load(f)

    bucket_name     = config["bucket_name"]
    results_location = config["results_location"].rstrip("/") + "/"
    athena_results   = config["athena_results_location"]
    domains_location = config.get("domains_location", "").rstrip("/") + "/"

    if not domains_location.startswith("s3://"):
        raise RuntimeError("domains_location must be an s3:// path")

    out_prefix = f"{results_location}{crawl_id}-cdx-json/"
    print(f"📦 Bucket: {bucket_name}")
    print(f"🗂️  Domains CSV prefix: {domains_location}")
    print(f"🎯 Target Crawl: {crawl_id} / subset={subset}")
    print(f"📤 Output prefix: {out_prefix}")
    print("✅ Filters: HTTP 200, text/html, latest capture per content_digest\n")

    start_ts = time.time()
    try:
        client = AthenaClient()

        # 0) Create domains_csv from single-column CSV + domains_norm
        print("0️⃣ Creating/validating domains tables...")
        create_domains_sql = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS default.domains_csv (
          domain STRING
        )
        ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
        WITH SERDEPROPERTIES (
          'separatorChar' = ',',
          'quoteChar'     = '"',
          'escapeChar'    = '\\\\'
        )
        LOCATION '{domains_location}'
        TBLPROPERTIES ('skip.header.line.count'='1');
        """
        client.execute_query(create_domains_sql, athena_results)

        create_view_sql = """
        CREATE OR REPLACE VIEW default.domains_norm AS
        SELECT
          REGEXP_REPLACE(LOWER(TRIM(domain)), '^www\\.', '') AS domain_norm
        FROM default.domains_csv
        WHERE domain IS NOT NULL AND TRIM(domain) <> '';
        """
        client.execute_query(create_view_sql, athena_results)

        # 1) Light table health checks
        print("1️⃣ Verifying domains...")
        q = "SELECT CAST(COUNT(*) AS BIGINT) AS cnt FROM default.domains_csv"
        qx = client.execute_query(q, athena_results)
        cnt = int(client.get_query_results(qx["QueryExecution"]["QueryExecutionId"])["rows"][0]["cnt"])
        if cnt == 0:
            raise RuntimeError("domains_csv is empty. Upload your domains first (single column header 'domain').")
        print(f"   ✅ domains_csv rows: {cnt}")

        # 2) Create ccindex table (idempotent) with official schema
        print("\n2️⃣ Creating/validating ccindex table...")
        ccindex_sql = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS default.ccindex (
          url_surtkey                STRING,
          url                        STRING,
          url_host_name              STRING,
          url_host_registered_domain STRING,
          url_protocol               STRING,
          url_port                   INT,
          url_path                   STRING,
          url_query                  STRING,
          fetch_time                 TIMESTAMP,
          fetch_status               SMALLINT,
          content_digest             STRING,
          content_mime_type          STRING,
          content_mime_detected      STRING,
          content_charset            STRING,
          content_languages          STRING,
          warc_filename              STRING,
          warc_record_offset         INT,
          warc_record_length         INT,
          warc_segment               STRING
        )
        PARTITIONED BY (crawl STRING, subset STRING)
        STORED AS PARQUET
        LOCATION 's3://commoncrawl/cc-index/table/cc-main/warc/';
        """
        client.execute_query(ccindex_sql, athena_results)
        print("   ✅ ccindex created/verified")

        # 3) Add ONLY the partition we need
        print("\n3️⃣ Adding target partition...")
        add_part_sql = f"""
        ALTER TABLE default.ccindex
        ADD IF NOT EXISTS PARTITION (crawl='{crawl_id}', subset='{subset}')
        LOCATION 's3://commoncrawl/cc-index/table/cc-main/warc/crawl={crawl_id}/subset={subset}/';
        """
        client.execute_query(add_part_sql, athena_results)
        print("   ✅ Partition add executed")

        # 4) Verify partition via metadata table (no data scan)
        print("\n4️⃣ Verifying partition (ccindex$partitions)...")
        verify_sql = f"""
        SELECT COUNT(1) AS cnt
        FROM "default"."ccindex$partitions"
        WHERE crawl='{crawl_id}' AND subset='{subset}';
        """
        vx = client.execute_query(verify_sql, athena_results)
        vrows = client.get_query_results(vx["QueryExecution"]["QueryExecutionId"])["rows"]
        if int(vrows[0]["cnt"]) == 0:
            raise RuntimeError(f"Partition crawl={crawl_id}, subset={subset} not found after ADD PARTITION.")
        print("   ✅ Partition present")

        # 5) UNLOAD JSONL: latest per digest, 200, HTML, dedup, safe JSON
        print("\n5️⃣ Exporting CDX-like JSON (latest per digest, 200, HTML)...")
        print("   ⏱️ Expected: ~1–3 minutes for modest outputs; more if the result set is huge")
        print("   💰 Athena scan: typically $0.05–$0.30; worst case ~$1.50 if you scan most of the crawl")

        export_sql = f"""
        UNLOAD (
          WITH ranked AS (
            SELECT
              cc.url_surtkey                                         AS urlkey,
              date_format(cc.fetch_time, '%Y%m%d%H%i%s')             AS timestamp,
              cc.url                                                 AS url,
              cc.content_mime_type                                   AS mime,
              cc.content_mime_detected                               AS mime_detected,
              CAST(cc.fetch_status AS VARCHAR)                       AS status,
              cc.content_digest                                      AS digest,
              CAST(cc.warc_record_length AS VARCHAR)                 AS length,
              CAST(cc.warc_record_offset AS VARCHAR)                 AS offset,
              cc.warc_filename                                       AS filename,
              cc.content_languages                                   AS languages,
              cc.content_charset                                     AS encoding,
              ROW_NUMBER() OVER (
                PARTITION BY cc.content_digest
                ORDER BY cc.fetch_time DESC
              ) AS rn
            FROM default.ccindex cc
            JOIN default.domains_norm d
              ON cc.url_host_registered_domain = d.domain_norm
            WHERE cc.crawl  = '{crawl_id}'
              AND cc.subset = '{subset}'
              AND cc.fetch_status = 200
              AND cc.content_mime_detected = 'text/html'
              AND cc.content_digest IS NOT NULL
              AND cc.url IS NOT NULL
          )
          SELECT
            CONCAT(
              '{{',
              '"urlkey":"', urlkey, '",',
              '"timestamp":"', timestamp, '",',
              '"url":"', REPLACE(REPLACE(url, '"', '\\\\"'), '\\n', '\\\\n'), '",',
              '"mime":"', COALESCE(mime,''), '",',
              '"mime-detected":"', COALESCE(mime_detected,''), '",',
              '"status":"', status, '",',
              '"digest":"', digest, '",',
              '"length":"', length, '",',
              '"offset":"', offset, '",',
              '"filename":"', filename, '",',
              '"languages":"', COALESCE(languages,''), '",',
              '"encoding":"', COALESCE(encoding,''), '"',
              '}}'
            ) AS cdx_record
          FROM ranked
          WHERE rn = 1
        )
        TO '{out_prefix}'
        WITH (
          format='TEXTFILE',
          compression='GZIP'
        );
        """
        print(f"   📤 Writing to: {out_prefix}")
        ex = client.execute_query(export_sql, athena_results)
        _ = client.get_query_results(ex["QueryExecution"]["QueryExecutionId"])
        print("   ✅ Export finished")

        # Save export info
        config["last_cdx_export"] = {
            "crawl_id": crawl_id,
            "output_location": out_prefix,
            "export_type": "cdx_unique_200_latest_html",
            "execution_id": ex["QueryExecution"]["QueryExecutionId"],
        }
        with open("src/config/aws_config.json", "w") as f:
            json.dump(config, f, indent=2)

        total_s = time.time() - start_ts
        mins = int(total_s // 60)
        secs = int(total_s % 60)
        print("\n🎉 Done!")
        print(f"⏱️  Total runtime: {mins}m {secs}s")
        print(f"📁 Results in: {out_prefix}")
        print("💾 Format: JSON lines (.gz), one record per line")
        print("🔎 Preview locally:")
        print("   aws s3 sync " + out_prefix + " ./cdx-results/")
        print("   zcat ./cdx-results/*.gz | head -n 5")

        return 0

    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
