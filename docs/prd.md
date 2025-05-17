# **Vibe Digest – Product Requirements Document (PRD)**

## **Overview**

**Vibe Digest** is an automated content aggregation and summarization tool that delivers curated, daily email digests of the most relevant developments in AI, developer tools, and emerging technology. Designed for busy tech founders, engineers, and AI practitioners, it ensures you stay informed without sifting through countless sources.

---

## **Problem Statement**

The velocity of innovation in AI and software tooling has made it increasingly difficult to stay current. Valuable insights are scattered across blogs, forums, and newsletters. Monitoring these sources manually is inefficient.
**Vibe Digest** solves this by programmatically aggregating and summarizing the most relevant updates into a concise, daily email digest.

---

## **Goals & Success Criteria**

### 🧭 Product Goals

* Reduce time spent scanning news and blog posts
* Improve signal-to-noise ratio for readers
* Enable lightweight consumption of critical developments in AI/code tooling

### 📊 Success Metrics

* **Open rate > 50%**
* **CTR on links > 10%**
* **Daily content freshness > 90%**
* **<1% failure rate across GitHub Action executions per week**

---

## **Core Features**

### 1. 🔍 Content Aggregation

* Fetches and parses content from prioritized sources:

  * Cursor Blog
  * Windsurf Blog
  * Latent Space
  * Reddit https://www.reddit.com/r/vibecoding/ (and others)
  * Hacker News (tagged for AI, dev tools, and programming)

---

## **Technical Architecture**

### 🧱 System Components

| Component        | Responsibility                                                                 |
| ---------------- | ------------------------------------------------------------------------------ |
| `GitHub Actions` | Orchestrates daily runs at 9 AM ET, handles logging & errors                   |
| `vibe_digest.py` | Core script for data fetch, summarization, HTML generation, and email dispatch |
| `tests/`         | Unit tests, mock inputs, linting (PEP8 + pylint)                               |
| `DynamoDB/Aurora`| Stores daily digests with date-keyed records                                   |
| `Lambda/API`     | CRUD endpoints for inserting and retrieving digests                            |
| `Web UI`         | “History” page to display past digests                                         |

#### Data Persistence Architecture Notes

- **AWS Service**: Use DynamoDB (preferred for serverless, scalable, and high-durability needs) or Aurora if relational features are required.
- **Table Design**: Table keyed by `date` (YYYY-MM-DD). Attributes: `feed_source`, `title`, `url`, `summary`, `timestamp`.
- **API Endpoints**:
  - `POST /digest` (Lambda): Insert new daily digest records
  - `GET /digest/{date}` (Lambda): Retrieve digest by date
  - `GET /digest` (Lambda): List digests over a date range
- **Web UI**: “History” page fetches and displays digests by date, with fast query and rendering.
- **Security**: Apply least-privilege IAM roles for Lambda access. Enable point-in-time recovery for DynamoDB.

---

## **Success Metrics**

* **Open rate > 50%**
* **CTR on links > 10%**
* **Daily content freshness > 90%**
* **<1% failure rate across GitHub Action executions per week**
* **Digest retrieval latency < 1 second**
* **Data durability ≥ 99.9%**
* **Web “History” page loads in < 500 ms**

---

## **Setup Instructions**

1. **Clone Repository**

   ```bash
   git clone <your-repo-url>
   cd vibe-digest
   ```

2. **Add GitHub Secrets**

   * Navigate to **Settings > Secrets and variables > Actions**
   * Add all secrets listed above

3. **Trigger Manual Run**

   * Go to **Actions** tab
   * Select **Vibe Coding Digest**
   * Click **Run workflow**

---

## **Sample Output**

```html
<h2>🧠 Vibe Digest – May 16, 2025</h2>
<ul>
  <li><strong>Title:</strong> New AI Features Released<br>
  <em>Source: Cursor Blog</em><br>
  Summary of the article content...<br>
  <a href="https://cursor.so/article-link">Read more →</a></li>
  <!-- Additional entries -->
</ul>
```

---

## **Reliability & Monitoring**

### ✅ Error Handling

* Retry logic for network/API timeouts
* Graceful degradation if one source fails
* Email delivery failure reporting

### 📊 Monitoring

* GitHub Actions status notifications
* SendGrid delivery tracking (opens, bounces)
* API usage metrics logged for OpenAI and SendGrid

## **Changelog**

### v1.0.0 – 2025-05-16

* 🎉 Initial Release
* Features: Daily content fetch, GPT-4 summaries, SendGrid email delivery
* GitHub Actions + Python-based automation
