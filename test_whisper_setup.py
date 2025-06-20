import os
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
WHISPER_CPP_DIR = "whisper.cpp"
WHISPER_CLI_PATH = os.path.join(WHISPER_CPP_DIR, "build/bin/whisper-cli")
MODEL_PATH = os.path.join(WHISPER_CPP_DIR, "models/ggml-base.en.bin")
SAMPLE_AUDIO_PATH = os.path.join(WHISPER_CPP_DIR, "samples/jfk.wav")
# ---

def verify_setup():
    """
    Verifies the whisper.cpp setup by checking for the binary and model,
    and then runs a test transcription.
    """
    logging.info("Starting whisper.cpp setup verification...")

    # 1. Check for whisper.cpp binary
    logging.info(f"Checking for whisper binary at: {WHISPER_CLI_PATH}")
    if not os.path.exists(WHISPER_CLI_PATH):
        logging.error("Whisper CLI binary not found. Please build whisper.cpp first.")
        logging.error("Build command: `cd whisper.cpp && make`")
        return False
    logging.info("Whisper binary found.")

    # 2. Check for model file
    logging.info(f"Checking for model file at: {MODEL_PATH}")
    if not os.path.exists(MODEL_PATH):
        logging.error("Model file not found. Please download the 'base.en' model.")
        logging.error("Download command: `bash whisper.cpp/models/download-ggml-model.sh base.en`")
        return False
    logging.info("Model file found.")

    # 3. Test transcription
    logging.info(f"Testing transcription with sample audio: {SAMPLE_AUDIO_PATH}")
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        logging.error(f"Sample audio file not found at: {SAMPLE_AUDIO_PATH}")
        return False
    
    transcription_command = [
        f"./build/bin/whisper-cli",
        "-m", "models/ggml-base.en.bin",
        "-f", "samples/jfk.wav",
        "--output-txt" # To get a text file output
    ]

    try:
        logging.info(f"Running command: {' '.join(transcription_command)}")
        # We run the command from within the whisper.cpp directory
        process = subprocess.run(
            transcription_command,
            cwd=WHISPER_CPP_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("Transcription command executed successfully.")
        logging.info("--- Transcription Output ---")
        # The transcription is printed to stderr by whisper.cpp
        print(process.stderr)
        logging.info("--------------------------")

        # Check for the output file
        output_txt_path = os.path.join(WHISPER_CPP_DIR, "samples/jfk.wav.txt")
        if os.path.exists(output_txt_path):
            logging.info(f"Transcription output file created at: {output_txt_path}")
            with open(output_txt_path, 'r') as f:
                transcription = f.read()
            logging.info(f"Transcription content: {transcription.strip()}")
            os.remove(output_txt_path) # Clean up the output file
            logging.info("Cleaned up transcription output file.")
        else:
            logging.warning("Transcription output file not found, but command seemed to succeed.")
            logging.warning("Whisper.cpp might have changed its output behavior.")


    except FileNotFoundError:
        logging.error(f"Error: The command could not be found. Is '{WHISPER_CLI_PATH}' correct and executable?")
        return False
    except subprocess.CalledProcessError as e:
        logging.error("Transcription command failed.")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"Output:\n{e.stderr}")
        return False

    logging.info("Verification successful! whisper.cpp is set up correctly.")
    return True

if __name__ == "__main__":
    if verify_setup():
        print("\n✅ Dicto setup verification PASSED.")
    else:
        print("\n❌ Dicto setup verification FAILED. Please check the logs.") 