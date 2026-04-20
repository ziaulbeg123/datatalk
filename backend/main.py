import os
import io
import uuid
import json

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# .env file se key load karo
load_dotenv()

app = FastAPI(title="DataTalk API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client — FREE!
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Memory mein sessions
sessions = {}


class QuestionRequest(BaseModel):
    session_id: str
    question: str


@app.get("/")
def root():
    return {"message": "DataTalk API chal raha hai ✅"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls', '.tsv')):
        raise HTTPException(400, "Sirf CSV, Excel ya TSV file supported hai.")

    contents = await file.read()

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.tsv'):
            df = pd.read_csv(io.BytesIO(contents), sep='\t')
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"File read nahi hui: {str(e)}")

    df = df.head(50000)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "df": df,
        "filename": file.filename,
        "history": [],
        "summary": get_df_summary(df)
    }

    return {
        "session_id": session_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(3).fillna("").to_dict(orient="records")
    }


@app.post("/ask")
async def ask_question(req: QuestionRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session nahi mila. File dobara upload karo.")

    df = session["df"]
    summary = session["summary"]
    history = session["history"]

    system_prompt = f"""You are DataTalk, an expert data analyst AI.

The user uploaded a dataset with this structure:
{summary}

Your job:
1. Answer the user's question clearly and concisely.
2. If a chart would help, include a chart block in this exact format:
<chart>
{{
  "type": "bar",
  "labels": ["A", "B", "C"],
  "values": [100, 200, 150],
  "title": "Chart Title"
}}
</chart>

Available chart types: bar, line, pie, scatter
If no chart needed, skip the chart block.
Keep answers short and friendly.
"""

    messages = [{"role": "system", "content": system_prompt}]

    for h in history[-6:]:
        messages.append({"role": "user", "content": h["question"]})
        messages.append({"role": "assistant", "content": h["answer"]})

    data_context = compute_context(df, req.question)
    messages.append({
        "role": "user",
        "content": f"{req.question}\n\nRelevant data:\n{data_context}"
    })

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Free + powerful model
            messages=messages,
            max_tokens=800
        )
        answer_text = response.choices[0].message.content

    except Exception as e:
        raise HTTPException(500, f"AI error: {str(e)}")

    # Chart parse karo
    chart_data = None
    chart_type = None
    clean_answer = answer_text

    if "<chart>" in answer_text:
        try:
            chart_json_str = answer_text.split("<chart>")[1].split("</chart>")[0].strip()
            chart_obj = json.loads(chart_json_str)
            chart_data = {
                "labels": chart_obj.get("labels", []),
                "values": chart_obj.get("values", []),
                "title": chart_obj.get("title", "")
            }
            chart_type = chart_obj.get("type", "bar")
            clean_answer = answer_text.split("<chart>")[0].strip()
        except:
            pass

    session["history"].append({
        "question": req.question,
        "answer": clean_answer
    })

    return {
        "answer": clean_answer,
        "chart_data": chart_data,
        "chart_type": chart_type
    }


@app.get("/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session nahi mila.")
    return {
        "filename": session["filename"],
        "rows": len(session["df"]),
        "columns": list(session["df"].columns),
        "history": session["history"]
    }


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"message": "Session delete ho gaya."}


def get_df_summary(df: pd.DataFrame) -> str:
    lines = []
    lines.append(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("\nColumn details:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        if df[col].dtype in ['int64', 'float64']:
            lines.append(
                f"  - {col} ({dtype}): min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
            )
        else:
            top_vals = df[col].value_counts().head(5).to_dict()
            lines.append(f"  - {col} ({dtype}): top values = {top_vals}")
    return "\n".join(lines)


def compute_context(df: pd.DataFrame, question: str) -> str:
    context_parts = []
    q_lower = question.lower()
    num_cols = df.select_dtypes(include='number').columns.tolist()

    if num_cols and any(w in q_lower for w in [
        'total', 'sum', 'revenue', 'sales', 'count',
        'average', 'mean', 'max', 'min', 'highest', 'lowest', 'top'
    ]):
        context_parts.append("Numeric stats:")
        context_parts.append(df[num_cols].describe().to_string())

    cat_cols = df.select_dtypes(include='object').columns.tolist()
    for col in cat_cols[:3]:
        context_parts.append(f"\nTop values in '{col}':")
        context_parts.append(df[col].value_counts().head(10).to_string())

    if not context_parts:
        context_parts.append(df.describe(include='all').to_string())

    return "\n".join(context_parts)[:3000]
