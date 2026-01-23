# Lekhaslides

A full-stack application for generating educational presentation slides by overlaying text on chalkboard backgrounds.

## Architecture

- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: Python FastAPI with PIL/Pillow for image generation
- **File Flow**: Upload files → Parse & generate → Download PPTX

## Project Structure

```
scm-slide-generator/
├── frontend/                 # React app
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── PreviewCard.tsx
│   │   │   ├── ConfigPanel.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── DownloadButton.tsx
│   │   ├── services/
│   │   │   └── api.ts       # API integration
│   │   ├── types/
│   │   │   └── index.ts     # TypeScript types
│   │   ├── App.tsx          # Main app
│   │   └── index.css        # Tailwind styles
│   └── package.json
├── backend/                  # Python FastAPI
│   ├── main.py              # FastAPI app & routes
│   ├── slide_generator.py   # PIL image generation
│   ├── docx_parser.py       # Parse Word docs
│   ├── pptx_builder.py      # Build PPTX files
│   └── fonts/
│       └── Caveat-Bold.ttf  # Downloaded (290KB)
├── start-fullstack.sh       # Start both servers
├── start-backend.sh         # Backend only
└── requirements.txt
```

---

## 🚀 Quick Start (Full Stack)

Run both frontend and backend together:

```bash
cd scm-slide-generator
./start-fullstack.sh
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Backend Setup

### 1. Create Virtual Environment

```bash
cd scm-slide-generator
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Font

The Caveat-Bold font is already downloaded in `backend/fonts/`

### 4. Run Backend Only

```bash
./start-backend.sh
# OR
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Frontend Only

```bash
npm run dev
```

Frontend runs on http://localhost:5173

### 3. Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

---

## Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **react-hot-toast** - Notifications
- **lucide-react** - Icons

### Backend
- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **python-pptx** - PowerPoint file creation
- **python-docx** - Word document parsing
- **Pillow** - Image processing
- **python-multipart** - File upload handling

---

## 🎨 Features

### 1. File Upload Section
- ✅ Drag-and-drop file upload
- ✅ Background image (chalkboard texture) with preview
- ✅ .docx file with questions
- ✅ File size display

### 2. Configuration Panel
- ✅ Instructor Name (default: "Mayank Agarwal")
- ✅ Subtitle (default: "{ Basics with Knowledge }")
- ✅ Badge Text (default: "Make Your own Concept")

### 3. Preview Section
- ✅ Parse questions from .docx
- ✅ Show total questions found
- ✅ Expandable question list
- ✅ Preview first slide
- ✅ Approve & generate all slides button

### 4. Generation & Download
- ✅ Progress indicator
- ✅ PPTX generation
- ✅ Download functionality
- ✅ Success confirmation
- ✅ Reset to create new presentation

### 5. Styling
- ✅ Dark chalkboard theme
- ✅ Orange/yellow/mint accent colors
- ✅ Card-based layout
- ✅ Responsive design
- ✅ Loading states & animations
- ✅ Toast notifications

---

## API Endpoints

### POST `/api/parse-docx`
Parse .docx file and extract structured questions

### POST `/api/generate-preview`
Generate preview image for first question

### POST `/api/generate-pptx`
Generate complete PPTX with all slides

### GET `/health`
Health check endpoint

See full API documentation at http://localhost:8000/docs

---

## Application Walkthrough

### 1. Content Preparation
To ensure your slides are generated correctly, format your `.docx` file as follows:

- **Questions**: Must start with a number followed by a dot or space (e.g., `1. What is SCM?` or `**1. What is SCM?**`).
- **Pointers**: Use bullet points for answers.
  - Format: `Label: Content` (e.g., `Definition: SCM is the proactive use...`).
  - If no colon is present, the text will appear without a bold label.
- **Bold Text**: Asterisks `**` are extracted and handled automatically.

### 2. Upload Files
- Upload your **chalkboard background image** (JPG/PNG).
- Upload your formatted **Questions Document** (.docx).
- Click **"Process Files & Generate Preview"**.

### 3. Review Preview
- Check the extracted question count.
- Review the list of parsed questions to ensure accuracy.
- Preview the generated slide text and layout.
- Adjust the **Instructor Name** and **Subtitle** in the configuration panel.

### 4. Generate Slides
- Click **"Approve & Generate All Slides"**.
- The system will process each question and overlay it onto the background.

### 5. Download Presentation
- Once complete, click **"Download Lekhaslides_Presentation.pptx"**.
- Open the file in PowerPoint or Google Slides to present.

### 6. Create New
- Click **"Create New Presentation"** to reset and start over throughout the app.

---

## Development

### Frontend Development
```bash
cd frontend
npm run dev    # Development server
npm run build  # Production build
npm run lint   # Run linter
```

### Backend Development
```bash
cd backend
uvicorn main:app --reload  # Hot reload enabled
```

### Testing
Test the API using the interactive docs at http://localhost:8000/docs

---

## Notes

- Backend CORS configured for all origins (adjust for production)
- Frontend proxies API requests to localhost:8000
- Font files must be in `backend/fonts/` directory
- Questions in .docx must be numbered (e.g., "1. Question text...")
- Bullet points should have labels followed by colons

---

## Next Steps

1. ✅ Backend implementation
2. ✅ Frontend development
3. ⏳ End-to-end testing
4. ⏳ Production deployment

---

**Built with ❤️ for education**
