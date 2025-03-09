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
    model = WhisperModel("small")
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

@app.route("/uploaded" , methods=["GET","POST"])
def upload():
    if(request.method == "POST"):
        if "file" not in request.files:
            return "no file part"
        file = request.files["file"]
        if(file.filename == ""):
            return "no selected file"
        
        file_path = os.path.join("static//uploads", file.filename)
        file.save(file_path)
        
        # try:   
        clip = mp.VideoFileClip(file_path)
        if(clip.audio):
            filename = os.path.splitext(file.filename)[0] 
            clip.audio.write_audiofile(f"static//audios//{filename}.mp3")
            subtitles = transcribe(f"static//audios//{filename}.mp3")
            save_srt(subtitles,f"static//srt_files//{filename}.srt")
            return redirect(f"/srtfiledownload/{filename}")
            # return file.filename.srt
        else:
            return "no audio available in this file"
        # except Exception as e:
        #     return f"Error processing file: {e}"
# app.config["debug"] = True


@app.route("/srtfiledownload/<filename>")
def srt_file_download(filename):
    return render_template("download.html", filename=filename)

@app.route("/download/<filename>")
def download_srt(filename):
    srt_path = os.path.join("static//srt_files", filename+".srt")
    
    return send_file(srt_path, as_attachment=True)

def cleanup_files():
    """Deletes all files from static/uploads, static/srt_files, and static/audios."""
    for folder in ["static//uploads", "static//srt_files","static//audios"]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
                
if __name__ == "__main__":
    app.run()