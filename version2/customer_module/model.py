import tensorflow as tf

# Load MobileNetV2 (pretrained on ImageNet) without its head
base_model = tf.keras.applications.MobileNetV2(
    weights="imagenet",
    include_top=False,
    pooling="avg",
    input_shape=(224, 224, 3)
)

# Preprocess function
def preprocess(img):
    img = tf.image.resize(img, (224, 224))
    img = tf.keras.applications.mobilenet_v2.preprocess_input(img)
    return img

# Extract features from an image path
def extract_features(path):
    img = tf.keras.utils.load_img(path)
    img = tf.keras.utils.img_to_array(img)
    img = preprocess(img)
    img = tf.expand_dims(img, 0)  # add batch dimension
    features = base_model(img)
    return features.numpy()[0]   # return vector
