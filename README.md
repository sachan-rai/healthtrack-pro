# 🏋️ HealthTrack Pro

A comprehensive wellness planning application that combines evidence-based nutrition guidance with personalized meal planning and workout recommendations.

## ✨ Features

- **🎯 Personalized Wellness Plans**: Generate 3-day meal and workout plans tailored to your specific goals
- **🥗 Comprehensive Recipe Database**: 70+ healthy recipes across multiple dietary restrictions
- **📊 Detailed Nutritional Information**: Complete macro breakdowns, ingredients, and dietary tags
- **🏃‍♂️ Evidence-Based Workouts**: AI-generated workout plans with specific exercises and durations
- **🌱 Multiple Dietary Options**: Support for Vegan, Vegetarian, Gluten-Free, Dairy-Free, Low-Carb, Keto, and Paleo diets
- **📱 Clean Web Interface**: Modern, responsive design with toggle-able meal details
- **🔍 RAG-Powered Recommendations**: Uses retrieval-augmented generation for evidence-based guidance

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sachan-rai/healthtrack-pro.git
   cd healthtrack-pro
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Build the knowledge index**
   ```bash
   python -m app.ingest.build_index
   ```

6. **Start the application**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Open your browser**
   Navigate to `http://localhost:8000`

## 📋 Usage

1. **Enter your wellness goal** (e.g., "lose weight", "build muscle", "maintain health")
2. **Fill in optional profile information**:
   - Age
   - Weight (kg)
   - Height (cm)
   - Dietary restrictions
3. **Click "Generate Plan"** to create your personalized 3-day plan
4. **Toggle meal details** to see ingredients, macros, and nutritional information
5. **Follow your plan** with detailed workouts and meal recommendations

## 🍽️ Recipe Database

The application includes 70+ carefully curated recipes across multiple dietary categories:

- **🌱 Vegan**: 18 recipes (Buddha bowls, lentil curries, plant-based proteins)
- **🥚 Vegetarian**: 20+ recipes (includes vegan options)
- **🌾 Gluten-Free**: 20+ recipes (pancakes, pasta, baked goods)
- **🥛 Dairy-Free**: 10 recipes (coconut curries, cashew alfredo)
- **🥬 Low-Carb**: 12 recipes (cauliflower rice, zucchini noodles)
- **🥑 Keto**: 10 recipes (fat bombs, bulletproof coffee, keto lasagna)
- **🦕 Paleo**: 10 recipes (grilled proteins, sweet potato hash)

Each recipe includes:
- Complete nutritional breakdown (calories, macros)
- Detailed ingredient lists
- Cuisine type and dietary tags
- Meal categories (breakfast, lunch, dinner, snack)

## 🏗️ Architecture

### Backend (FastAPI)
- **RAG Pipeline**: Retrieval-augmented generation for evidence-based recommendations
- **Vector Database**: ChromaDB for storing and retrieving wellness guidelines
- **Recipe Management**: JSON-based recipe database with filtering capabilities
- **API Endpoints**: RESTful API for plan generation and admin functions

### Frontend (HTML/CSS/JavaScript)
- **Responsive Design**: Clean, modern interface that works on all devices
- **Interactive Features**: Toggle meal details, form validation, loading states
- **Real-time Updates**: Dynamic content loading and error handling

### Data Sources
- **Nutritional Guidelines**: PDF documents from authoritative sources
- **Recipe Database**: Curated collection of healthy, diverse recipes
- **Evidence Base**: Scientific guidelines for physical activity and nutrition

## 📁 Project Structure

```
healthtrack-pro/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── main.py                # FastAPI application
│   ├── data/                  # Knowledge base and recipes
│   │   ├── recipes.json       # Recipe database
│   │   └── *.pdf              # Nutritional guidelines
│   ├── ingest/                # Data ingestion pipeline
│   │   ├── build_index.py     # Vector database builder
│   │   └── loaders.py         # Document loaders
│   └── rag/                   # RAG pipeline
│       ├── pipeline.py        # Main planning logic
│       └── prompts.py         # AI prompts
├── index.html                 # Web interface
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI-powered recommendations
- `CHROMA_PERSIST_DIR`: Vector database storage location (default: `.chroma_store`)
- `EMBED_MODEL`: OpenAI embedding model (default: `text-embedding-3-small`)
- `CHAT_MODEL`: OpenAI chat model (default: `gpt-4o-mini`)

### Customization
- **Add Recipes**: Edit `app/data/recipes.json` to include new recipes
- **Update Guidelines**: Add PDF documents to `app/data/` and rebuild the index
- **Modify Prompts**: Adjust AI behavior in `app/rag/prompts.py`

## 🚀 Deployment

### Local Development
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Deployment
- **Heroku**: Add `Procfile` with `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Railway**: Deploy directly from GitHub
- **AWS/GCP**: Use container services or serverless functions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to new functions
- Include docstrings for new modules
- Test new features thoroughly
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: For providing the AI models that power the recommendations
- **LangChain**: For the RAG framework and document processing
- **ChromaDB**: For vector database capabilities
- **FastAPI**: For the modern, fast web framework
- **Nutritional Guidelines**: Based on official dietary and physical activity recommendations

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/sachan-rai/healthtrack-pro/issues) page
2. Create a new issue with detailed information
3. Contact: [sachan.rai@example.com](mailto:sachan.rai@example.com)

## 🔮 Roadmap

- [ ] **User Authentication**: Save and track personal progress
- [ ] **Extended Planning**: 7-day and 30-day plan options
- [ ] **Recipe Scaling**: Adjust portions based on user needs
- [ ] **Workout Videos**: Integration with exercise demonstration videos
- [ ] **Progress Tracking**: Weight, measurements, and goal tracking
- [ ] **Social Features**: Share plans and recipes with community
- [ ] **Mobile App**: Native iOS and Android applications
- [ ] **AI Personalization**: Learn from user preferences and feedback

---

**Made with ❤️ for healthier living**
