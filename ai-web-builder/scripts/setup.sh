#!/bin/bash

# AI Web Builder Development Environment Setup Script

echo "🚀 Setting up AI Web Builder development environment..."

# Check if running on Windows (WSL)
if grep -q Microsoft /proc/version; then
    echo "✅ Detected WSL environment"
fi

# Check Node.js version
NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
if [[ $NODE_VERSION == "not installed" ]]; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js version: $NODE_VERSION"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "not installed")
if [[ $PYTHON_VERSION == "not installed" ]]; then
    echo "❌ Python not found. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Install root dependencies
echo "📦 Installing all workspace dependencies with pnpm..."
export PNPM_HOME="/home/gman/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
pnpm install

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Copy environment files
echo "📄 Setting up environment files..."
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local"
fi

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
fi

# Build shared package
echo "🔨 Building shared package..."
pnpm --filter shared build

# Set up Git hooks (optional)
echo "🔧 Setting up Git hooks..."
if [ -d ".git" ]; then
    # Pre-commit hook for linting
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
echo "Running pre-commit checks..."

# Run frontend linting
pnpm --filter frontend lint
if [ $? -ne 0 ]; then
    echo "❌ Frontend linting failed"
    exit 1
fi

# Run type checking
pnpm type-check
if [ $? -ne 0 ]; then
    echo "❌ Type checking failed"
    exit 1
fi

echo "✅ Pre-commit checks passed"
EOF
    chmod +x .git/hooks/pre-commit
    echo "✅ Git pre-commit hook installed"
fi

# Create development database (Docker)
echo "🐘 Setting up development database..."
if command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL and Redis with Docker..."
    docker-compose up -d postgres redis
    echo "✅ Database services started"
else
    echo "⚠️  Docker Compose not found. Please start PostgreSQL and Redis manually."
fi

# Final setup instructions
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add your API keys to backend/.env:"
echo "   - OPENAI_API_KEY=your-key-here"
echo "   - ANTHROPIC_API_KEY=your-key-here"
echo ""
echo "2. Start the development servers:"
echo "   pnpm dev"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "   pnpm dev             # Start both frontend and backend"
echo "   pnpm build           # Build for production"
echo "   pnpm lint            # Run code linting"
echo "   pnpm type-check      # Run TypeScript checking"
echo ""
echo "Happy coding! 🚀"