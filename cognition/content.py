"""
Content Creation Toolkit — generates articles, marketing copy,
social media posts, emails, and other written content.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContentTemplate:
    name: str
    description: str
    prompt_template: str
    output_format: str = "text"
    variables: list[str] = field(default_factory=list)


class ContentCreator:
    """Advanced content creation engine with templates for various content types."""

    def __init__(self) -> None:
        self._templates = self._init_templates()

    def _init_templates(self) -> dict[str, ContentTemplate]:
        return {
            "blog_post": ContentTemplate(
                name="Blog Post",
                description="SEO-optimized blog post with structured sections",
                prompt_template="""Write a comprehensive blog post about {topic}.
Target audience: {audience}
Tone: {tone}
Word count target: {word_count}
Include:
- Compelling headline
- Introduction hook
- {sections} main sections with H2/H3 headings
- Practical examples or case studies
- Actionable takeaways
- Strong conclusion with CTA

SEO keywords to include: {keywords}""",
                variables=["topic", "audience", "tone", "word_count", "sections", "keywords"],
            ),
            "email_sequence": ContentTemplate(
                name="Email Sequence",
                description="Multi-email nurture or sales sequence",
                prompt_template="""Create an email sequence for: {purpose}
Sequence length: {num_emails} emails
Product/Service: {product}
Target audience: {audience}
Tone: {tone}

For each email provide:
- Subject line (+ 1 alternative)
- Preview text
- Email body
- CTA button text
- Send timing recommendation""",
                variables=["purpose", "num_emails", "product", "audience", "tone"],
            ),
            "social_media": ContentTemplate(
                name="Social Media Post",
                description="Platform-optimized social media content",
                prompt_template="""Create {num_posts} social media posts for: {topic}
Platform: {platform}
Tone: {tone}
Include:
- Hook/first line
- Main content
- Hashtags (relevant, trending)
- CTA or engagement prompt
- Optimal posting time suggestion""",
                variables=["topic", "platform", "tone", "num_posts"],
            ),
            "landing_page": ContentTemplate(
                name="Landing Page Copy",
                description="High-converting landing page content",
                prompt_template="""Write landing page copy for: {product/service}
Target audience: {audience}
Main benefit: {benefit}
Price point: {price}
Include:
- Hero headline + subheadline
- Pain points section (3-4 problems)
- Solution section
- Features with benefits (not just specs)
- Social proof framework
- FAQ section (5-8 questions)
- Multiple CTA variations
- Urgency/scarcity elements""",
                variables=["product/service", "audience", "benefit", "price"],
            ),
            "technical_article": ContentTemplate(
                name="Technical Article",
                description="In-depth technical content with code examples",
                prompt_template="""Write a technical article about: {topic}
Audience level: {level} (beginner/intermediate/advanced)
Include:
- Overview and prerequisites
- Core concepts explained
- Step-by-step implementation
- Code examples in {language}
- Common pitfalls and solutions
- Performance considerations
- Further reading resources""",
                variables=["topic", "level", "language"],
            ),
            "product_description": ContentTemplate(
                name="Product Description",
                description="Persuasive product description for e-commerce",
                prompt_template="""Write product descriptions for: {product}
Target buyer: {audience}
Key features: {features}
Price range: {price_range}
Include:
- Short description (50 words)
- Medium description (150 words)
- Long description (300+ words)
- Bullet-point features
- Specifications list
- Size/dimension guide
- What's in the box""",
                variables=["product", "audience", "features", "price_range"],
            ),
            "press_release": ContentTemplate(
                name="Press Release",
                description="Professional press release format",
                prompt_template="""Write a press release about: {news}
Company: {company}
Date: {date}
Location: {location}

Follow AP press release format:
- Compelling headline
- Subheadline
- Dateline lead paragraph (who, what, when, where, why)
- Supporting details
- Quote from key stakeholder
- Company boilerplate
- Media contact info""",
                variables=["news", "company", "date", "location"],
            ),
            "report_executive": ContentTemplate(
                name="Executive Report",
                description="Professional executive summary or report",
                prompt_template="""Write an executive report on: {topic}
Organization: {organization}
Time period: {period}
Audience: {audience}

Include:
- Executive summary (1 page)
- Key findings
- Data analysis narrative
- Recommendations (prioritized)
- Implementation timeline
- Risk assessment
- Conclusion""",
                variables=["topic", "organization", "period", "audience"],
            ),
            "business_proposal": ContentTemplate(
                name="Business Proposal",
                description="Persuasive business proposal",
                prompt_template="""Write a business proposal for: {project}
Client: {client}
Our company: {company}
Budget range: {budget}
Timeline: {timeline}

Include:
- Cover page text
- Executive summary
- Problem statement
- Proposed solution
- Methodology/approach
- Timeline and milestones
- Pricing structure
- Team qualifications
- Case studies/references
- Terms and conditions outline""",
                variables=["project", "client", "company", "budget", "timeline"],
            ),
            "video_script": ContentTemplate(
                name="Video Script",
                description="YouTube/social media video script",
                prompt_template="""Write a video script for: {topic}
Platform: {platform}
Duration: {duration}
Style: {style} (educational/entertaining/promotional)

Include:
- Hook (first 5 seconds)
- Introduction
- Main content with time stamps
- B-roll suggestions
- On-screen text/graphics
- CTA
- Outro""",
                variables=["topic", "platform", "duration", "style"],
            ),
        }

    def get_template(self, name: str) -> ContentTemplate | None:
        return self._templates.get(name)

    def list_templates(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description, "variables": ", ".join(t.variables)}
            for t in self._templates.values()
        ]

    def generate_prompt(
        self, template_name: str, **kwargs: Any
    ) -> dict[str, str]:
        """Generate a content creation prompt from template + variables."""
        template = self._templates.get(template_name)
        if not template:
            return {"error": f"Unknown template: {template_name}"}

        missing = [v for v in template.variables if v not in kwargs]
        if missing:
            return {"error": f"Missing variables: {', '.join(missing)}"}

        prompt = template.prompt_template
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return {"prompt": prompt, "template": template.name, "format": template.output_format}

    def adapt_tone(self, text: str, target_tone: str) -> str:
        """Return instructions for adapting text to a target tone."""
        tone_instructions = {
            "professional": "Rewrite in a professional, authoritative tone. Remove casual language, use precise vocabulary, maintain formal structure.",
            "casual": "Rewrite in a casual, conversational tone. Use contractions, shorter sentences, and friendly language.",
            "persuasive": "Rewrite to be more persuasive. Use power words, emotional appeals, strong CTAs, and benefit-focused language.",
            "informative": "Rewrite to be purely informative. Remove opinions, focus on facts, use clear and objective language.",
            "humorous": "Rewrite with humor. Add witty observations, playful language, and light-hearted metaphors.",
            "empathetic": "Rewrite with empathy. Acknowledge feelings, use supportive language, show understanding.",
            "authoritative": "Rewrite to establish authority. Use confident statements, cite expertise, remove hedging language.",
        }
        return tone_instructions.get(target_tone, f"No tone instructions for: {target_tone}")

    def create_content_plan(self, topic: str, goal: str, channels: list[str]) -> dict[str, Any]:
        """Generate a content plan across multiple channels."""
        plan: dict[str, Any] = {
            "topic": topic,
            "goal": goal,
            "channels": {},
        }

        channel_templates = {
            "blog": {"template": "blog_post", "frequency": "Weekly", "word_count": "1500-2500"},
            "twitter": {"template": "social_media", "frequency": "Daily", "posts_per_day": 3},
            "linkedin": {"template": "social_media", "frequency": "3x/week", "style": "professional"},
            "email": {"template": "email_sequence", "frequency": "Bi-weekly", "sequence_length": 5},
            "youtube": {"template": "video_script", "frequency": "Weekly", "duration": "8-12 min"},
            "instagram": {"template": "social_media", "frequency": "Daily", "format": "carousel/reel"},
            "tiktok": {"template": "video_script", "frequency": "3x/week", "duration": "30-60s"},
        }

        for channel in channels:
            ch_lower = channel.lower()
            if ch_lower in channel_templates:
                plan["channels"][channel] = channel_templates[ch_lower]

        return plan
