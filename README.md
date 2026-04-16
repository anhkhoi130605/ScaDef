🔍 Scam Detection System (Multimodal)

This repository contains the implementation, dataset structure, and training pipeline for a multimodal scam detection system, focusing on detecting fraudulent content from text, audio, and URL sources.

The system is designed to support real-world scam detection scenarios such as:

Phone call scams
Fraudulent messages
Malicious / phishing links
🚀 Key Features
🔤 Text-based scam detection (NLP - Transformer models)
🔊 Audio scam detection (speech-to-text + semantic analysis)
🌐 URL / Link analysis (phishing detection, domain features)
🧠 Multimodal fusion (combine multiple inputs)
📊 Scam classification by category
📂 Dataset Structure

The system is designed with a multi-table / multi-source dataset architecture:

🔗 InputSource (Main Table)
Field	Description
id	Unique ID
user_id	User reference
source_type	text / audio / link
created_at	Timestamp
📝 Text Data
Field	Description
text_id	ID
source_id	FK → InputSource
content	Input text
🔊 Audio Data
Field	Description
audio_id	ID
source_id	FK
file_path	Audio file
transcript	Speech-to-text result
🌐 Link Data
Field	Description
link_id	ID
source_id	FK
url	Input URL
domain_age	Domain age
risk_score	Calculated risk
🏷️ Scam Categories
Label_id	Category
0	Normal
1	Gambling
2	Adult / Sexual Services
3	Fake Credentials
4	Fake Banking
5	Drugs
6	Cash-out Fraud
7	Fake Certification
8	SIM Scam
9	Loan Scam
10	Other
⚙️ Dependencies
Python 3.10+
PyTorch 2.1+
Transformers
ffmpeg (for audio processing)
librosa / pydub
🧠 Model Architecture
1. Text Model
PhoBERT / BERT / Qwen
Output: embedding + classification
2. Audio Model
Speech-to-text → text pipeline
Optional: wav2vec2 / Whisper
3. Link Model
Domain-based features:
Domain age
URL length
Suspicious patterns
4. Multimodal Fusion
Concatenate embeddings
Feed into classifier (MLP / Transformer)
🏋️ Training
Step 1: Clone repository
git clone <your-repo-link>
cd scam-detection
Step 2: Prepare dataset
Insert data into database (SQL Server / PostgreSQL)
Or export to JSON / CSV
Step 3: Train model
sh run.sh
🧪 Example Data
Label_id   Text
0          Hôm nay trời đẹp, đi uống cà phê không?
8          Bán SIM không cần đăng ký chính chủ, liên hệ Zalo 09xxxx
9          Vay tiền nhanh không cần thế chấp, lãi suất thấp
📈 Future Improvements
🔍 Real-time scam detection API
📞 Call center integration
🧬 Graph-based fraud detection
🤖 LLM-based reasoning (RAG + prompt engineering)
📚 References

If you use this idea, you can refer to:

ChiFraud: A Long-term Web Text Benchmark for Chinese Fraud Detection
Multimodal NLP research papers
📌 Citation
@project{scam_detection_system,
  title={Multimodal Scam Detection System},
  author={Your Name},
  year={2026}
}
👨‍💻 Author
Your Name
Project: Scam Detection System
Focus: AI Security / Fraud Detection
⚠️ Disclaimer

This project is for research and educational purposes only.
Do not use it for illegal or unethical activities.