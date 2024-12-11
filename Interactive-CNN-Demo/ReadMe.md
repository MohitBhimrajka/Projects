# 🔢 MNIST Digit Classifier

An interactive web application for handwritten digit recognition using a Convolutional Neural Network (CNN) trained on the MNIST dataset.

1. Install Dependencies

pip install -r requirements.txt


2. Run the App

streamlit run app.py

The app will open in your browser at http://localhost:8501/.

Additional Details:

Description
This app demonstrates the power of deep learning in recognizing handwritten digits. Utilizing TensorFlow and Keras, the CNN model achieves high accuracy on the MNIST dataset, a benchmark in machine learning.

📂 File Structure

- app.py: Main application script.
- requirements.txt: List of required Python packages.
- atlas_logo.png: University logo for the sidebar.
- mnist_sample.png: Sample image displayed on the home page.
- README.md: This file.

💡 How to Use
- Training the Model
    - Navigate to Train Model.
    - Click Train New Model.
        - Wait for training to complete (may take a few minutes).
        - View the test accuracy and training plots.
    - Live Demo
        - Go to Live Demo.
        - Choose Draw or Upload:
        - Draw: Sketch a digit on the canvas.
        - Upload: Upload an image of a handwritten digit.
T
The model will predict the digit and display the probabilities.

🛠️ Troubleshooting

- Dependencies Error: Ensure all packages are installed with pip install -r requirements.txt.
- Canvas Issues: Verify streamlit-drawable-canvas is installed.
- Model Loading Delay: The model may take a moment to load due to caching.