# Common Crawl Documentation

## What is Common Crawl?

Common Crawl is a non-profit organization that crawls the web and freely provides its archives and datasets to the public. Since 2008, Common Crawl has been building a repository of web crawl data that is openly accessible to researchers, businesses, and developers worldwide.

### Key Facts
- **Founded**: 2008
- **Frequency**: Monthly crawls
- **Scale**: 3+ billion web pages per crawl
- **Data Size**: ~90TB per crawl (compressed)
- **Format**: WARC, WET, WAT files
- **Access**: Free via AWS S3
- **Cost**: Pay only AWS data transfer costs

### Mission
To democratize web data by making it freely available for research, analysis, and innovation.

## Common Crawl Data Formats

Common Crawl provides three main file formats, each serving different use cases:

### 1. WARC Files (Web ARChive)
**Purpose**: Complete web page captures including HTTP headers, HTML content, and metadata.

**Structure**:
```
WARC/1.0
WARC-Type: response
WARC-Target-URI: https://example.com/page
WARC-Date: 2025-01-30T12:34:56Z
WARC-Record-ID: <urn:uuid:12345678-1234-5678-9abc-123456789abc>
Content-Type: application/http; msgtype=response
Content-Length: 2048

HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 1536

<!DOCTYPE html>
<html>
<head>
    <title>Example Page</title>
</head>
<body>
    <h1>Welcome to Example.com</h1>
    <p>This is a sample page...</p>
</body>
</html>
```

**Use Cases**:
- Full website analysis
- Web archive preservation
- Complete HTTP transaction research
- SEO and content analysis

### 2. WET Files (Web Extracted Text)
**Purpose**: Plain text content extracted from web pages, without HTML markup.

**Structure**:
```
WARC/1.0
WARC-Type: conversion
WARC-Target-URI: https://example.com/page
WARC-Date: 2025-01-30T12:34:56Z
WARC-Record-ID: <urn:uuid:87654321-4321-8765-bcda-987654321abc>
Content-Type: text/plain
Content-Length: 156

Welcome to Example.com

This is a sample page with some text content.
The text has been extracted from the HTML
and is provided in plain text format.
```

**Use Cases**:
- Natural language processing
- Text mining and analysis
- Content research
- Machine learning training data

### 3. WAT Files (Web Attribute Text)
**Purpose**: Metadata and structured information about web pages in JSON format.

**Structure**:
```json
{
  "Envelope": {
    "WARC-Header-Metadata": {
      "WARC-Type": "metadata",
      "WARC-Target-URI": "https://example.com/page",
      "WARC-Date": "2025-01-30T12:34:56Z",
      "WARC-Record-ID": "<urn:uuid:abcdef12-3456-7890-abcd-1234567890ef>",
      "Content-Type": "application/json"
    },
    "Payload-Metadata": {
      "HTTP-Response-Metadata": {
        "Status-Code": 200,
        "Headers": {
          "Content-Type": "text/html; charset=utf-8",
          "Server": "nginx/1.18.0",
          "Content-Length": "1536"
        }
      },
      "HTML-Metadata": {
        "Title": "Example Page",
        "Meta": [
          {
            "name": "description",
            "content": "This is an example page"
          }
        ],
        "Links": [
          {
            "url": "https://example.com/about",
            "text": "About Us"
          }
        ]
      }
    }
  }
}
```

**Use Cases**:
- Website structure analysis
- Link graph construction
- SEO metadata research
- HTTP header analysis

## CDX Index Files

CDX (Canonical URL and Timestamp with Digest) files provide an index of all crawled URLs, making it easier to find specific content without downloading entire WARC files.

### CDX Format Example:
```
com,example)/page 20250130123456 https://example.com/page text/html 200 sha1:ABC123DEF456 1536 12345 CC-MAIN-20250130120000-warc.gz
```

### CDX Fields:
- **URL Key**: Canonicalized URL (domain reversed)
- **Timestamp**: Crawl time (YYYYMMDDHHMMSS)
- **Original URL**: Full URL as crawled
- **MIME Type**: Content type
- **Status Code**: HTTP response code
- **Content Digest**: SHA1 hash of content
- **Length**: Content length in bytes
- **Offset**: Position in WARC file
- **Filename**: WARC file containing the record

## Frequently Asked Questions

### 🤔 What Can Common Crawl Do?

**Q: Can Common Crawl crawl JavaScript-rendered content?**
**A: No.** Common Crawl uses traditional HTTP crawlers that only capture the initial HTML response from servers. It does not execute JavaScript, so any content that requires JavaScript rendering (Single Page Applications, dynamic content, AJAX-loaded data) will not be captured. You'll only get the raw HTML sent by the server.

**Q: Does Common Crawl respect robots.txt files?**
**A: Yes.** Common Crawl strictly follows robots.txt directives. If a website's robots.txt file prohibits crawling for any user agent (or specifically for Common Crawl), those pages will not be crawled or included in the datasets.

**Q: How often does Common Crawl visit the same page?**
**A: Multiple times.** Common Crawl may visit the same URL several times during a single crawl or across different monthly crawls. This results in multiple versions of the same page with different timestamps. **Always use the latest capture per content digest** to avoid duplicates when analyzing data.

**Q: Can I get real-time or recent data?**
**A: No.** Common Crawl publishes datasets with a delay. Monthly crawls are typically published 1-3 months after the crawl completion. For real-time data, you'll need to implement your own crawling solution.

### 🚫 What Common Crawl Cannot Do

**Q: Can it crawl websites protected by authentication?**
**A: No.** Common Crawl cannot access any content that requires:
- Login credentials
- Authentication tokens
- Session cookies
- API keys
- OAuth flows

This includes private social media profiles, member-only content, and password-protected sites.

**Q: Can it crawl social media platforms like LinkedIn, Twitter/X, Facebook?**
**A: Limited or No.** Most major social media platforms either:
- Block crawlers in their robots.txt
- Require authentication for meaningful content
- Use JavaScript-heavy interfaces that Common Crawl cannot render
- Implement anti-bot measures

Examples of typically inaccessible platforms:
- LinkedIn profiles and posts
- Twitter/X tweets (protected by robots.txt)
- Facebook posts and profiles
- Instagram content
- TikTok videos
- Private Discord servers

**Q: Can it crawl dynamic, AJAX-loaded content?**
**A: No.** Content that loads after the initial page load via:
- AJAX requests
- Fetch API calls
- WebSocket connections
- JavaScript DOM manipulation

Will not be captured in Common Crawl data.

**Q: Can it access geo-restricted content?**
**A: No.** Common Crawl crawlers operate from specific geographic locations and IP ranges. Content that is geo-blocked or shows different versions based on location may not be accessible or may only show the version visible to Common Crawl's crawler locations.

### 📊 Understanding Data Quality

**Q: Why do I see multiple entries for the same URL?**
**A: Temporal captures.** Common Crawl may visit the same URL multiple times during a crawl period. Each visit creates a new record with a different timestamp. Reasons include:
- Following different link paths to the same page
- Periodic re-crawling during the monthly cycle
- Content updates detected by the crawler

**Recommendation**: Use content digest (SHA1 hash) to identify unique content and keep only the latest capture per digest.

**Q: How reliable is the crawled content?**
**A: Variable quality.** Common Crawl data quality depends on:
- Server response reliability
- Network conditions during crawl
- Website availability and performance
- Anti-bot measures implemented by sites

Always validate and filter data based on HTTP status codes, content types, and content length.

### 🔍 Technical Limitations

**Q: What file formats can Common Crawl handle?**
**A: Primarily web content.** Common Crawl focuses on:
- HTML pages (text/html)
- Plain text files (text/plain)
- Some document formats (PDF, DOC, etc.)

It does NOT effectively handle:
- Binary files (images, videos)
- Application-specific formats
- Streaming content
- Real-time data feeds

**Q: How does Common Crawl handle redirects?**
**A: Follows HTTP redirects.** Common Crawl follows standard HTTP redirects (301, 302) but records both the original URL and the final destination. Check the WARC records for complete redirect chains.

**Q: Can I control what Common Crawl crawls?**
**A: No direct control.** Common Crawl operates independently and you cannot:
- Request specific URLs to be crawled
- Exclude your site from future crawls (except via robots.txt)
- Control crawl frequency or timing
- Access crawl data in real-time

### 💡 Best Practices

**Q: How should I handle duplicate content?**
**A: Use content digests.** Always deduplicate using the SHA1 content digest field and prefer the latest timestamp when multiple captures exist for the same content.

**Q: What's the most efficient way to analyze large datasets?**
**A: Use CDX indices.** Instead of downloading full WARC files:
1. Query CDX indices to find relevant URLs
2. Download only specific WARC records you need
3. Use AWS Athena for large-scale filtering (as this tool does)

**Q: How can I estimate crawl coverage for my domain?**
**A: Check multiple crawls.** Coverage varies significantly between crawls. Check several monthly crawls to understand:
- Which pages are consistently crawled
- Crawl frequency patterns
- Coverage gaps and limitations

This tool automatically handles many of these best practices by filtering for successful responses (HTTP 200), deduplicating by content digest, and focusing on HTML content only.