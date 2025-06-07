# AI Engineering Feed Migration Guide

This guide helps you transition your Vibe Coding Digest to focus specifically on AI Engineers and vibe coders.

## Overview

The new configuration focuses on:
- **AI-Assisted Development Tools**: Cursor, Windsurf, Claude Code, GitHub Copilot, etc.
- **AI Engineering Practices**: Prompt engineering, RAG pipelines, LLMOps
- **AI Frameworks**: LangChain, LlamaIndex, AutoGen, CrewAI
- **Community Discussions**: Focused on AI development and engineering

## Migration Steps

### 1. Backup Current Configuration
```bash
cp feeds_config.json feeds_config_backup.json
```

### 2. Apply New AI Engineering Configuration
```bash
cp feeds_config_ai_engineering.json feeds_config.json
```

### 3. Update AWS Blog Search (Optional)
To enhance AWS blog searches with AI engineering focus:
```python
# In src/vibe_digest.py, update the import:
from src.ai_engineering_search import fetch_aws_blog_posts
```

### 4. Test the New Configuration
```bash
./run.sh test
python -m src.vibe_digest
```

## Key Changes

### New Feed Categories
- **AI Tools**: Cursor, Windsurf, Claude Code, Copilot releases and discussions
- **AI Engineering**: LLM engineering, prompt engineering, RAG content
- **AI Frameworks**: LangChain, LlamaIndex, AutoGen updates
- **Community**: Focused subreddits like r/AIDevelopment, r/LocalLLaMA

### Disabled Feeds
The following generic feeds are disabled but retained for easy re-enabling:
- r/programming
- r/artificial
- r/MachineLearning
- Towards Data Science

### Enhanced Search Queries
The new search system prioritizes:
1. Tool comparisons (Cursor vs Windsurf)
2. Practical tutorials and guides
3. Performance benchmarks
4. Cost optimization strategies
5. New feature announcements

## Relevance Scoring

Content is now scored based on:
- **Base Score**: Number of matched AI engineering terms (10 points each)
- **Comparison Bonus**: +5 points for tool comparisons
- **Practical Bonus**: +3 points for tutorials/guides
- **Performance Bonus**: +3 points for benchmarks/optimization
- **Freshness Bonus**: +2 points for new releases/updates

## Customization Options

### Add Custom Queries
```json
{
  "url": "https://hnrss.org/newest?q=YOUR+QUERY&points=20",
  "source_name": "Hacker News: Your Query",
  "category": "Custom",
  "enabled": true
}
```

### Adjust Relevance Threshold
In `ai_engineering_search.py`:
```python
# Increase for stricter filtering
min_relevance_score = 15.0  # Default: 10.0
```

### Monitor Specific GitHub Projects
Add to feeds_config.json:
```json
{
  "url": "https://github.com/ORG/REPO/releases.atom",
  "source_name": "GitHub: Project Name",
  "category": "AI Tools",
  "enabled": true
}
```

## Recommended YouTube Channels

The configuration includes AI-focused channels:
- **AI Explained**: Deep dives into AI concepts
- **Matt Wolfe**: AI tools and news
- **Fireship**: Dev + AI content
- **Andrej Karpathy**: Technical AI content
- **Latent Space**: AI engineering podcast

## Performance Tips

1. **Enable/Disable Feeds**: Set `"enabled": false` for feeds you want to temporarily exclude
2. **Category Filtering**: Use categories to organize and potentially filter content
3. **Custom Scoring**: Modify `_calculate_relevance_score()` to match your priorities

## Monitoring Results

After migration, monitor:
1. **Content Quality**: Are you getting relevant AI engineering content?
2. **Coverage**: Are important tools/topics being missed?
3. **Noise Level**: Too much irrelevant content?

Adjust queries and scoring accordingly.

## Rollback

To revert to the original configuration:
```bash
cp feeds_config_backup.json feeds_config.json
```

## Future Enhancements

Consider adding:
1. **Discord/Slack Integration**: Monitor AI engineering communities
2. **Twitter/X Lists**: Follow AI engineering thought leaders
3. **Conference Feeds**: AI engineering conference updates
4. **Paper Feeds**: ArXiv AI/ML papers relevant to engineering

---

Last Updated: 2025-01-07