from flask import Flask,render_template,request,redirect,send_file
import moviepy as mp
import os
from faster_whisper import WhisperModel


def format_timestamp(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def save_srt(subtitles, srt_filename):
    """Save subtitles as an SRT file."""
    with open(srt_filename, "w", encoding="utf-8") as f:
        f.writelines(subtitles)
        
def transcribe(audio_path):
    model = WhisperModel("tiny")
    segments, info = model.transcribe(audio_path)
    language = info.language
    print("Transcription language", language)
    
    subtitle_data = []
    index = 1
    for segment in segments:
        start_time = format_timestamp(segment.start)
        end_time = format_timestamp(segment.end)
        text = segment.text.strip()

        subtitle_data.append(f"\n{index}\n{start_time} --> {end_time}\n{text}\n")
        index += 1

    return subtitle_data


app = Flask(__name__)

@app.route("/")
def home():
    return """ 
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Home</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
                background-image: url('static//img//bgimg.jpg');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                color: black;
            }
            .btn {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                font-size: 16px;
                transition: background 0.3s;
            }
            .btn:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>WELCOME TO ALL</h1>
        <p>Click the button below to upload a file:</p>
        <a href="/fileupload" class="btn">Upload File</a>
    </body>
    </html>
    """

@app.route("/fileupload")
def upload_file():
    return render_template("uploadfile.html")

@app.route("/uploaded", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part"
    
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    
    upload_dir = "tmp"
    
    # Ensure the tmp directory exists
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    
    clip = mp.VideoFileClip(file_path)
    if clip.audio:
        filename = os.path.splitext(file.filename)[0] 
        audio_path = os.path.join(upload_dir, f"{filename}.mp3")
        srt_path = os.path.join(upload_dir, f"{filename}.srt")
        
        clip.audio.write_audiofile(audio_path)
        subtitles = transcribe(audio_path)
        save_srt(subtitles, srt_path)

        return redirect(f"/srtfiledownload/{filename}")
    else:
        return "No audio available in this file"


@app.route("/srtfiledownload/<filename>")
def srt_file_download(filename):
    return render_template("download.html", filename=filename)

@app.route("/download/<filename>")
def download_srt(filename):
    srt_path = os.path.join("tmp", filename + ".srt") 
    
    if not os.path.exists(srt_path):
        return "File not found", 404
    
    return send_file(srt_path, as_attachment=True, download_name=f"{filename}.srt")
                
if __name__ == "__main__":
    app.run()