import streamlit as st
import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image, ImageOps
from streamlit_drawable_canvas import st_canvas
import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Set Streamlit page configuration
st.set_page_config(
    page_title="MNIST Digit Classifier",
    page_icon="🔢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load university logo
logo_image = Image.open("atlas_logo.png")

# CSS styling
st.markdown(
    """
    <style>
    .main { background-color: #f0f3f4; }
    .title { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
    .subtitle { color: #34495e; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
    .stButton>button { background-color: #2980b9; color: white; font-size: 18px; padding: 10px 20px; }
    .header-img { max-width: 150px; }
    .sidebar .sidebar-content { background-color: #2980b9; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.image(logo_image, caption="ATLAS SkillTech University", use_column_width=True)
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to", ["Home", "Train Model", "Live Demo", "About"])

# Function to load and preprocess MNIST data
@st.cache_resource
def load_and_preprocess_data():
    """
    Load and preprocess the MNIST dataset.
    Returns:
        (x_train, y_train), (x_test, y_test): Preprocessed training and testing data.
    """
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
    # Normalize and reshape data
    x_train = x_train.reshape(-1, 28, 28, 1).astype('float32') / 255.0
    x_test = x_test.reshape(-1, 28, 28, 1).astype('float32') / 255.0
    return (x_train, y_train), (x_test, y_test)

# Function to create the CNN model
def create_model():
    """
    Create a Convolutional Neural Network model for MNIST digit classification.
    Returns:
        model: Compiled CNN model.
    """
    model = keras.Sequential([
        keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
        keras.layers.MaxPooling2D((2, 2)),
        keras.layers.Conv2D(64, (3, 3), activation='relu'),
        keras.layers.MaxPooling2D((2, 2)),
        keras.layers.Conv2D(64, (3, 3), activation='relu'),
        keras.layers.Flatten(),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dense(10, activation='softmax'),
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

# Function to train the model
@st.cache_resource
def train_model():
    """
    Train the CNN model on the MNIST dataset.
    Returns:
        model: Trained CNN model.
        history: Training history object.
        test_acc: Test accuracy on the MNIST test dataset.
    """
    (x_train, y_train), (x_test, y_test) = load_and_preprocess_data()
    model = create_model()

    # Define callbacks
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.0001)
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    # Train the model
    history = model.fit(
        x_train, y_train,
        epochs=20,
        validation_split=0.1,
        callbacks=[reduce_lr, early_stopping],
        verbose=0
    )

    # Evaluate the model on the test set
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test accuracy: {test_acc:.4f}")

    return model, history, test_acc

# Function to preprocess images
def preprocess_image(image, is_drawn=False):
    """
    Preprocess the uploaded or drawn image for prediction.
    Args:
        image: Input image.
        is_drawn (bool): Flag indicating if the image was drawn on the canvas.
    Returns:
        image: Preprocessed image ready for prediction.
    """
    if is_drawn:
        # Convert canvas data to PIL image
        image = Image.fromarray(image.astype('uint8'), 'RGBA')
        image = image.convert('L')
        image = ImageOps.invert(image)
    else:
        image = image.convert('L')
        image = ImageOps.invert(image)

    # Resize and normalize image
    image = image.resize((28, 28))
    image = np.array(image).astype('float32') / 255.0
    image = np.expand_dims(image, axis=-1)
    return image

# Function to plot training history
def plot_training_history(history):
    """
    Plot the training and validation accuracy and loss.
    Args:
        history: Training history object.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Plot accuracy
    ax1.plot(history.history['accuracy'], label='Training Accuracy')
    ax1.plot(history.history['val_accuracy'], label='Validation Accuracy')
    ax1.set_title('Model Accuracy')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()

    # Plot loss
    ax2.plot(history.history['loss'], label='Training Loss')
    ax2.plot(history.history['val_loss'], label='Validation Loss')
    ax2.set_title('Model Loss')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()

    st.pyplot(fig)

# Main application logic
def main():
    if app_mode == "Home":
        st.markdown("<h1 class='title'>🔢 MNIST Digit Classifier</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitle'>Handwritten Digit Recognition with Deep Learning</h3>", unsafe_allow_html=True)

        st.image("mnist_sample.png", caption="MNIST Handwritten Digits", use_column_width=True)

        st.write("""
            Welcome to the MNIST Digit Classifier! This app demonstrates handwritten digit recognition using a Convolutional Neural Network (CNN) trained on the MNIST dataset.

            **Features:**
            - Train a CNN model on the MNIST dataset
            - Test the model by drawing digits or uploading images
            - Visualize model performance and predictions

            Navigate through the app using the sidebar to explore these features!
        """)

    elif app_mode == "Train Model":
        st.header("Train Model")
        if st.button("Train New Model"):
            with st.spinner("Training model... This may take a few minutes."):
                model, history, test_acc = train_model()
            st.success(f"Model trained successfully! Test accuracy: {test_acc:.4f}")
            plot_training_history(history)
        else:
            st.info("Click the button to train a new model.")

    elif app_mode == "Live Demo":
        st.header("Live Demo")
        st.write("Note: The model may take a few moments to load if not already cached.")
        # Load the model
        model, _, _ = train_model()

        option = st.radio("Choose input method:", ["Draw", "Upload"])

        if option == "Draw":
            st.write("Draw a digit in the box below:")
            canvas_result = st_canvas(
                stroke_width=20,
                stroke_color="#FFFFFF",
                background_color="#000000",
                height=280,
                width=280,
                drawing_mode="freedraw",
                key="canvas",
            )

            if canvas_result.image_data is not None:
                img = canvas_result.image_data
                img = preprocess_image(img, is_drawn=True)
                prediction = model.predict(np.expand_dims(img, axis=0))[0]
                predicted_digit = np.argmax(prediction)
                st.write(f"Predicted digit: **{predicted_digit}**")
                st.bar_chart(prediction)

        else:
            uploaded_file = st.file_uploader("Upload an image of a digit...", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                img = preprocess_image(image)
                prediction = model.predict(np.expand_dims(img, axis=0))[0]
                predicted_digit = np.argmax(prediction)
                st.write(f"Predicted digit: **{predicted_digit}**")
                st.bar_chart(prediction)

    elif app_mode == "About":
        st.header("About")
        st.write("""
            This app uses a Convolutional Neural Network (CNN) to recognize handwritten digits from the MNIST dataset.

            The MNIST dataset consists of 70,000 images of handwritten digits, split into 60,000 training images and 10,000 testing images.
            Each image is a 28x28 grayscale representation of a digit from 0 to 9.

            The CNN model used in this app is trained on this dataset to learn to recognize and classify these handwritten digits.

            **Created by Your Name using TensorFlow, Keras, and Streamlit.**
        """)

    st.sidebar.markdown("---")
    st.sidebar.info("MNIST Digit Classifier v1.0")

if __name__ == "__main__":
    main()
