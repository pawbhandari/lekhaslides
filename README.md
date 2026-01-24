# Lekhaslides

A full-stack application for generating beautiful educational presentation slides by overlaying handwritten-style text on chalkboard backgrounds. Perfect for teachers creating engaging classroom content.

## ✨ What's New (v2.0)

- 🔤 **Text Input Mode** - Paste questions directly, no file upload needed
- 🖊️ **4 Handwriting Fonts** - Chalk, Casual, Playful, and Natural styles
- 🎯 **Draggable Badge** - Position the badge anywhere on the slide
- 📏 **Pointer Spacing Control** - Fine-tune spacing between answer bullets
- ⚡ **4x Faster Generation** - Parallel processing with smart caching
- 📊 **Real-time Progress Bar** - Live updates during PPTX generation
- 🧹 **Auto Markdown Cleanup** - Removes `*`, `**`, `_` artifacts from text

## Architecture

- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: Python FastAPI with PIL/Pillow for image generation
- **Streaming**: Server-Sent Events (SSE) for real-time progress
- **File Flow**: Upload/Paste → Parse & preview → Generate → Download PPTX

## Project Structure

```
lekhaslides/
├── frontend/                 # React app
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── PreviewCard.tsx
│   │   │   ├── ConfigPanel.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── DownloadButton.tsx
│   │   ├── services/
│   │   │   └── api.ts       # API integration (with SSE support)
│   │   ├── types/
│   │   │   └── index.ts     # TypeScript types
│   │   ├── App.tsx          # Main app with draggable badge
│   │   └── index.css        # Tailwind styles
│   └── package.json
├── backend/                  # Python FastAPI
│   ├── main.py              # FastAPI app & routes (SSE streaming)
│   ├── slide_generator.py   # PIL image generation (with caching)
│   ├── docx_parser.py       # Parse Word docs & text
│   ├── pptx_builder.py      # Build PPTX files
│   └── fonts/               # Handwriting fonts
│       ├── PatrickHand-Regular.ttf   # Chalk style
│       ├── Caveat-Regular.ttf        # Casual style
│       ├── IndieFlower-Regular.ttf   # Playful style
│       └── Kalam-Regular.ttf         # Natural style
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

### 1. Input Flexibility
- ✅ **File Upload** - Drag-and-drop .docx file with questions
- ✅ **Text Paste** - Directly paste question content (no file needed)
- ✅ Background image upload with preview (supports standard & truncated images)
- ✅ Automatic markdown artifact cleanup (`*`, `**`, `_`, `__`)

### 2. Font Selection
- ✅ **Chalk** (Patrick Hand) - Classic chalkboard handwriting
- ✅ **Casual** (Caveat) - Relaxed, flowing script
- ✅ **Playful** (Indie Flower) - Fun, whimsical style
- ✅ **Natural** (Kalam) - Authentic handwritten feel

### 3. Configuration Panel
- ✅ Instructor Name (optional - leave empty to hide)
- ✅ Subtitle (optional - leave empty to hide)
- ✅ Badge Text (optional - leave empty to hide)
- ✅ Font Size controls (header & body)
- ✅ Position offsets (X and Y axis)
- ✅ **Pointer Spacing** slider (-50px to +100px)

### 4. Draggable Badge
- ✅ Click and drag badge to any position on preview
- ✅ Position saved automatically to config
- ✅ Badge position used in final PPTX generation

### 5. Preview Section
- ✅ Parse questions from .docx or pasted text
- ✅ Show total questions found
- ✅ Expandable question list
- ✅ **Half-resolution preview** for faster rendering
- ✅ 500ms debounce for real-time updates

### 6. Generation & Download
- ✅ **Real-time progress bar** with SSE streaming
- ✅ "Generating slide X of Y" status updates
- ✅ **Parallel processing** (4 workers) for 4x speed
- ✅ Font and background caching
- ✅ Download PPTX on completion
- ✅ Reset to create new presentation

### 7. Styling
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

### POST `/api/parse-text`
Parse raw text content and extract structured questions (new!)

### POST `/api/generate-preview`
Generate preview image for a question (half-resolution for speed)
- Supports `render_badge: false` for frontend overlay mode

### POST `/api/generate-pptx`
Generate complete PPTX with all slides
- **SSE Streaming** - Real-time progress events
- Returns base64-encoded PPTX data

### GET `/health`
Health check endpoint

See full API documentation at http://localhost:8000/docs

---

## Application Walkthrough

### 1. Content Preparation
Format your content as follows:

- **Questions**: Must start with a number followed by a dot or space (e.g., `1. What is SCM?`)
- **Pointers**: Use bullet points for answers
  - Format: `Label: Content` (e.g., `Definition: SCM is the proactive use...`)
  - If no colon is present, the text will appear without a bold label
- **Markdown**: Asterisks `*`, `**`, `_`, `__` are automatically cleaned

### 2. Input Your Content
**Option A: Upload File**
- Upload your formatted **Questions Document** (.docx)

**Option B: Paste Text**
- Click the "Paste Text" tab
- Paste your questions directly into the text area

Then:
- Upload your **chalkboard background image** (JPG/PNG)
- Click **"Process Files & Generate Preview"**

### 3. Customize Your Slides
- **Select Font Style**: Chalk, Casual, Playful, or Natural
- **Adjust Layout**: Use position sliders and pointer spacing
- **Drag Badge**: Click and drag the badge to your preferred position
- **Optional Elements**: Leave instructor name, subtitle, or badge empty to hide them

### 4. Review Preview
- Check the extracted question count
- Review the list of parsed questions
- Preview updates in real-time as you adjust settings

### 5. Generate Slides
- Click **"Approve & Generate All Slides"**
- Watch the real-time progress bar
- Each slide is generated in parallel for speed

### 6. Download Presentation
- Click **"Download Lekhaslides_Presentation.pptx"**
- Open in PowerPoint or Google Slides

### 7. Create New
- Click **"Create New Presentation"** to reset and start over

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
- Questions must be numbered (e.g., "1. Question text...")
- Bullet points should have labels followed by colons
- **Performance**: Uses font/background caching + parallel generation (4 workers)
- **Preview Mode**: Renders at 960x540 for speed, final PPTX at 1920x1080

---

## Changelog

### v2.1 (January 24, 2026) - Stability Update
- ✅ **Fix**: Resolved backend crash when rendering rotated text/badges
- ✅ **Fix**: Fixed background image caching issue (previews now update correctly)
- ✅ **Improvement**: Added support for truncated/incomplete image files
- ✅ **Verification**: Verified full slide generation workflow

### v2.0 (January 2026)
- ✅ Text input mode (paste directly)
- ✅ 4 handwriting font styles
- ✅ Draggable badge positioning
- ✅ Pointer spacing control
- ✅ Real-time SSE progress bar
- ✅ Parallel slide generation (4x faster)
- ✅ Font and background caching
- ✅ Markdown artifact cleanup
- ✅ Optional header elements

### v1.0
- ✅ Backend implementation
- ✅ Frontend development
- ✅ File upload & parsing
- ✅ PPTX generation

---

**Built with ❤️ for education**

