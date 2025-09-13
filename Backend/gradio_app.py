import gradio as gr
import requests

FLASK_URL = "http://127.0.0.1:5000"  # Your Flask backend

def submit_form(name, story, doc_type, aadhaar_number, pan_number, user_id,
                id_img, selfie_img, supporting_doc, aadhaar_doc, pan_doc):

    files = {
        "id_image": id_img,
        "selfie_image": selfie_img,
        "supporting_doc": supporting_doc,
        "aadhaar_doc": aadhaar_doc,
        "pan_doc": pan_doc
    }

    data = {
        "name": name,
        "story": story,
        "supporting_doc_type": doc_type,
        "aadhaar_number": aadhaar_number,
        "pan_number": pan_number,
        "user_id": user_id
    }

    try:
        res = requests.post(f"{FLASK_URL}/submit", data=data, files=files)
        if res.status_code == 200:
            return res.json()
        else:
            return {"error": f"Status {res.status_code}: {res.text}"}
    except Exception as e:
        return {"error": str(e)}

def get_records():
    try:
        res = requests.get(f"{FLASK_URL}/records")
        if res.status_code == 200:
            records = res.json().get("records", [])
            if not records:
                return "No records found."
            table = ""
            for r in records:
                table += f"ID: {r['id']}, Name: {r['name']}, Trust Score: {r['trust_score']}, Story Score: {r['emotion_score']}\n"
            return table
        else:
            return f"Status {res.status_code}: {res.text}"
    except Exception as e:
        return str(e)

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 🛡 Trust Score Verifier UI")

    with gr.Tab("Submit Trust Score"):
        with gr.Row():
            name = gr.Textbox(label="Full Name")
            user_id = gr.Textbox(label="User ID")
        story = gr.Textbox(label="Story", lines=5)
        doc_type = gr.Textbox(label="Supporting Document Type (e.g., license, certificate)")
        aadhaar_number = gr.Textbox(label="Aadhaar Number")
        pan_number = gr.Textbox(label="PAN Number")
        id_img = gr.File(label="ID Image", type="file")
        selfie_img = gr.File(label="Selfie Image", type="file")
        supporting_doc = gr.File(label="Supporting Document (PDF)", type="file")
        aadhaar_doc = gr.File(label="Aadhaar Card Image", type="file")
        pan_doc = gr.File(label="PAN Card Image", type="file")

        submit_btn = gr.Button("Submit for Verification")
        output = gr.JSON(label="Result")

        submit_btn.click(
            submit_form,
            inputs=[name, story, doc_type, aadhaar_number, pan_number, user_id,
                    id_img, selfie_img, supporting_doc, aadhaar_doc, pan_doc],
            outputs=output
        )

    with gr.Tab("View Records"):
        view_btn = gr.Button("Refresh Records")
        records_output = gr.Textbox(label="All Records", lines=10)
        view_btn.click(get_records, inputs=None, outputs=records_output)

demo.launch(server_name="0.0.0.0", server_port=7860)
