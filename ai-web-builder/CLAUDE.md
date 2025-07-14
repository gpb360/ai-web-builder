# Claude AI Assistant Instructions for AI Web Builder Platform

## Project Overview

You are the AI development assistant for building a **revolutionary AI-native marketing platform** that competes with GoHighLevel and Simvoly. This platform uses AI to automatically build complete marketing campaigns, allowing users to describe their needs and receive fully functional campaigns with minimal manual work.

## Core Mission

**Build the world's first AI-native marketing platform that eliminates complexity through intelligent automation.**

- **Primary Goal:** Create a platform where users describe their business and AI builds everything
- **Key Differentiator:** "AI builds it, you just tweak it" approach
- **Target Market:** SMBs frustrated with GoHighLevel's complexity
- **Business Model:** SaaS with 80%+ margins through efficient AI usage

## Technical Architecture

### Technology Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Zustand, React Query
- **Backend:** FastAPI (Python 3.11+), PostgreSQL, Redis, Celery
- **AI Integration:** Anthropic Claude (primary), OpenAI GPT-4/GPT-4V (fallback)
- **Infrastructure:** AWS (ECS, RDS, S3, CloudFront), Vercel (frontend)
- **Key APIs:** GoHighLevel, Simvoly, WordPress integration

### Project Structure
```
ai-web-builder/
├── frontend/           # Next.js application
├── backend/            # FastAPI server  
├── shared/             # Shared TypeScript types
├── docs/               # Documentation (PRD, tasks, etc.)
└── docker-compose.yml  # Development environment
```

## Development Priorities

### Phase 1 (Months 1-6): MVP Foundation
1. **Platform Integration:** GoHighLevel, Simvoly, WordPress API connections
2. **AI Analysis Engine:** Analyze existing campaigns and suggest improvements
3. **Enhancement Mode:** Improve existing campaigns without platform switching
4. **Export System:** Generate improvements in platform-compatible formats
5. **Migration Planning:** AI-powered migration assessment and planning

### Phase 2 (Months 7-12): Complete Migration Suite
1. **Full Migration Tools:** Automated platform migration capabilities
2. **Hybrid Operation:** Run old and new platforms simultaneously
3. **Advanced AI:** Custom model training and brand-aware generation
4. **Component Marketplace:** User-generated component ecosystem

### Phase 3 (Months 13-18): Complete Platform
1. **Native CRM:** Built-in customer relationship management
2. **E-commerce:** Product management and shopping capabilities
3. **Enterprise Features:** White-label, API access, advanced security

## AI Model Strategy & Cost Management

### Primary AI Stack
- **Claude 3.5 Sonnet:** Primary model ($0.18/campaign generation)
- **GPT-4 Turbo:** Fallback for reliability ($0.35/campaign)
- **GPT-4V:** Image analysis only ($0.027/image)
- **Local Models:** Llama 3.1 70B for basic tasks (cost optimization)

### Cost Optimization Rules
1. **Always use Claude first** - 50% cheaper than GPT-4
2. **Monitor costs in real-time** - alert if usage exceeds budget
3. **Implement intelligent caching** - reuse similar components
4. **Rate limiting** - prevent abuse and cost spikes
5. **Progressive model selection** - use cheapest model that can handle task

### Pricing Strategy (Must Maintain 80%+ Margins)
- **Creator Tier:** $49/month (25 campaigns, 86% margin)
- **Business Tier:** $149/month (100 campaigns, 84% margin)  
- **Agency Tier:** $399/month (500 campaigns, 67% margin)

## Development Standards

### Code Quality Requirements
1. **TypeScript Everywhere:** Strict typing, no `any` types
2. **Error Handling:** Comprehensive try-catch, user-friendly messages
3. **Performance First:** Optimize for speed, implement caching
4. **Security:** Input validation, SQL injection prevention, secure secrets
5. **Testing:** Unit tests for all utilities, integration tests for APIs

## Git Workflow - MANDATORY PROCESS

### **🚫 NEVER WORK DIRECTLY ON MAIN BRANCH**
- **Always create feature branches** for any work
- **Never commit directly to main** - all changes must go through Pull Requests
- **All code must be reviewed** before merging to main

### **Required Git Workflow Steps:**

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/feature-name
   # Example: git checkout -b feature/add-user-auth
   # Example: git checkout -b fix/hydration-errors
   # Example: git checkout -b enhancement/improve-performance
   ```

2. **Work on Feature:**
   ```bash
   # Make your changes
   git add .
   git commit -m "descriptive commit message"
   ```

3. **Push to Remote:**
   ```bash
   git push origin feature/feature-name
   ```

4. **Create Pull Request:**
   ```bash
   # Use GitHub CLI or web interface
   gh pr create --title "Feature: Add user authentication" --body "Description of changes"
   ```

5. **After PR Review & Approval:**
   ```bash
   # Merge through GitHub interface, then clean up
   git checkout main
   git pull origin main
   git branch -d feature/feature-name
   ```

### **Branch Naming Conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes  
- `enhancement/description` - Improvements to existing features
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### **Commit Message Format:**
```
type: Brief description of change

- Detailed explanation of what was changed
- Why the change was necessary
- Any breaking changes or important notes

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### **PR Requirements:**
- **Clear title and description** of what was changed
- **Link to related issues** if applicable
- **Test results** - confirm all tests pass
- **Screenshots** for UI changes
- **Breaking changes** clearly documented

### **Example Workflow:**
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/add-pricing-page

# Work on feature
# ... make changes ...
git add .
git commit -m "feat: Add pricing page with 3-tier structure"

# Push and create PR
git push origin feature/add-pricing-page
gh pr create --title "Feature: Add pricing page" --body "Adds 3-tier pricing structure with monthly/annual options"

# After approval and merge
git checkout main
git pull origin main
git branch -d feature/add-pricing-page
```

### **🔥 CRITICAL RULES:**
1. **NO DIRECT COMMITS TO MAIN** - Automatic rejection
2. **ALL FEATURES REQUIRE PR REVIEW** - No exceptions
3. **PUSH EARLY AND OFTEN** - Don't wait until feature is complete
4. **KEEP BRANCHES SMALL** - 1 feature per branch maximum
5. **DELETE BRANCHES AFTER MERGE** - Keep repository clean

### AI Integration Standards
1. **Cost Awareness:** Track and optimize every AI API call
2. **Fallback Systems:** Multiple model support for reliability
3. **Prompt Engineering:** Optimized prompts for quality and cost
4. **Response Validation:** Ensure AI outputs are safe and functional
5. **User Feedback Loop:** Learn from user corrections and preferences

### Component Generation Standards
1. **Production Ready:** All generated code must be deployment-ready
2. **Responsive Design:** Mobile-first approach, all screen sizes
3. **Accessibility:** WCAG 2.1 AA compliance built-in
4. **Performance:** Optimized for Core Web Vitals
5. **Brand Consistency:** Maintain visual identity across components

## Key Features to Implement

### 1. Platform Integration Analysis (Priority 1)
- Connect to GoHighLevel, Simvoly, WordPress APIs
- Analyze existing campaigns for improvement opportunities
- Generate comprehensive audit reports
- Provide step-by-step improvement plans

### 2. AI Enhancement Engine (Priority 1)  
- Generate improved versions of existing landing pages
- Create better-converting forms and email sequences
- Suggest new campaign components based on performance
- Export improvements in platform-compatible formats

### 3. Migration Planning System (Priority 2)
- AI-powered migration complexity analysis
- Create detailed migration timelines
- Risk assessment and mitigation strategies
- Side-by-side platform comparison tools

### 4. Component Generation System (Priority 2)
- Multi-modal AI (text + image input)
- React component generation with styling
- Real-time preview and editing
- Export to multiple formats (React, HTML/CSS, platform-specific)

### 5. Analytics & Performance Tracking (Priority 3)
- Component-level conversion tracking
- Real-time performance monitoring
- A/B testing automation
- ROI calculation and reporting

## User Experience Guidelines

### Simplicity Through Intelligence
1. **Natural Language Interface:** Users describe needs in plain English
2. **Minimal Clicks:** Complete campaigns in under 5 clicks
3. **Instant Results:** Show progress and results in real-time
4. **Smart Defaults:** AI chooses best options, user can override
5. **Progressive Disclosure:** Hide complexity until needed

### Migration User Flow
1. **Connect Existing Platform:** One-click API connection
2. **AI Analysis:** Comprehensive audit in under 2 minutes
3. **See Improvements:** Side-by-side comparison of suggested changes
4. **Try Enhancements:** Test improvements without switching platforms
5. **Gradual Migration:** Move when ready, not forced

## Testing Strategy

### Manual Testing Priorities
1. **AI Output Quality:** Every generated component must be functional
2. **Platform Integration:** Test with real GoHighLevel/Simvoly accounts
3. **Performance:** Load testing with realistic AI usage patterns
4. **Cost Tracking:** Ensure AI costs never exceed projections
5. **User Flow:** Complete end-to-end user journeys

### Automated Testing
1. **Unit Tests:** All utility functions and API integrations
2. **Integration Tests:** AI service interactions and error handling
3. **Security Tests:** Input validation and injection prevention
4. **Performance Tests:** Response times and resource usage
5. **Cost Tests:** AI usage tracking and budget enforcement

## Security & Compliance

### Data Protection
1. **User Data:** Encrypt all PII, minimal data collection
2. **API Keys:** Secure storage, regular rotation
3. **AI Inputs:** Sanitize all user inputs before AI processing
4. **Generated Code:** Security scan all AI-generated components
5. **Platform Access:** Secure OAuth for third-party integrations

### Business Continuity
1. **AI Service Outages:** Multiple model fallbacks
2. **Cost Overruns:** Automatic shutoffs and alerts
3. **Platform Changes:** Adaptive integration layer
4. **User Data:** Regular backups and disaster recovery
5. **Revenue Protection:** Usage monitoring and abuse prevention

## Success Metrics to Track

### Technical Metrics
- **AI Generation Success Rate:** >90% usable without modification
- **Response Times:** <5 minutes for complete campaigns
- **Cost Per Campaign:** <$0.25 average across all tiers
- **Platform Uptime:** 99.9% availability
- **User Satisfaction:** 4.5+ stars on AI output quality

### Business Metrics
- **Monthly Recurring Revenue:** Target $250K by month 12
- **Customer Acquisition Cost:** <$150 per customer
- **Gross Margin:** Maintain 80%+ across all plans
- **User Retention:** 95%+ annual retention rate
- **Upgrade Rate:** 60%+ from Creator to Business tier

## Common Tasks & Commands

### Git Workflow (ALWAYS FOLLOW)
```bash
# Start new feature (REQUIRED)
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Work and commit frequently
git add .
git commit -m "descriptive message"

# Push and create PR (REQUIRED)
git push origin feature/your-feature-name
gh pr create --title "Feature: Description" --body "Details"

# After PR approval
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

### Development Setup
```bash
# Start development environment
pnpm dev

# Run backend API
cd backend && uvicorn main:app --reload

# Run tests
pnpm test

# Check AI costs
pnpm run cost-check

# Deploy to staging
pnpm run deploy:staging
```

### AI Development
- **Always** implement cost tracking for new AI features
- **Test** with minimal API calls during development
- **Cache** similar requests to reduce costs
- **Monitor** real-time usage and set alerts
- **Document** prompt engineering decisions

### Platform Integration
- **Use** official APIs when available
- **Implement** rate limiting for external APIs
- **Handle** authentication renewal automatically
- **Parse** data into standardized formats
- **Test** with multiple account types

### 🚨 CRITICAL REMINDERS
- **NEVER COMMIT DIRECTLY TO MAIN** - Always use feature branches
- **ALWAYS CREATE PULL REQUESTS** - No exceptions for any changes
- **PUSH EARLY AND OFTEN** - Don't wait until feature is complete
- **TEST BEFORE PUSHING** - Ensure builds pass before creating PR

## When to Ask for Help

### Immediate Assistance Needed
1. **AI Cost Overruns:** If any AI feature exceeds budget projections
2. **Security Issues:** Any potential data or security vulnerabilities
3. **Platform API Changes:** When third-party APIs break or change
4. **Performance Problems:** Response times exceeding targets
5. **User Experience Issues:** Anything that breaks the "simplicity" promise

### Decision Points
1. **Technical Architecture:** Major structural decisions
2. **AI Model Selection:** Choosing between different AI approaches
3. **Feature Prioritization:** Balancing user needs vs development time
4. **Business Logic:** Pricing, billing, or subscription logic
5. **Integration Strategy:** How to handle platform-specific requirements

## Success Mantras

1. **"AI builds it, you tweak it"** - Minimize user effort through intelligence
2. **"Simplicity through intelligence"** - Hide complexity behind smart AI
3. **"Profitable growth only"** - Never sacrifice margins for features
4. **"User results first"** - Every feature must improve user outcomes
5. **"Migration made easy"** - Remove all friction from platform switching

Remember: You're building the platform that makes GoHighLevel's complexity obsolete through intelligent automation. Every line of code should advance that mission while maintaining profitable unit economics.

## Current Development Status

**✅ Completed:**
- Project structure and architecture
- Comprehensive PRD with market analysis
- Profitable pricing strategy (80%+ margins)
- AI cost analysis and optimization plan
- Detailed development task breakdown

**🔄 Next Priority:**
- Begin DEV-001: Development environment setup
- Implement DEV-002: Database schema design
- Start DEV-004: GoHighLevel API integration

**💰 Financial Targets:**
- Month 1-2: $5K-15K (pre-orders)
- Month 3-4: $25K-50K (beta launch)
- Month 5-6: $100K MRR (full launch)
- Month 12: $250K MRR ($3M ARR)