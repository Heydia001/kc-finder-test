import tensorflow as tf
import numpy as np
import os
import matplotlib.pyplot as plt
import time
import glob
from pathlib import Path

DATABASE_IMAGES_DIR = Path("C:/KDH/kc-finder-test/database_images/")
TARGET_IMAGES_DIR = Path("C:/KDH/kc-finder-test/target_images/")
RESULTS_DIR = Path("C:/KDH/kc-finder-test/tensorflow_results/")
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']

os.makedirs(DATABASE_IMAGES_DIR, exist_ok=True)
os.makedirs(TARGET_IMAGES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

base_model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, pooling='avg')
feature_extractor = tf.keras.Model(inputs=base_model.input, outputs=base_model.output)


def preprocess_image(image_path):
    try:
        img = tf.keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception:
        return None


def extract_features(image_paths):
    features = []
    valid_paths = []

    for path in image_paths:
        img_array = preprocess_image(path)
        if img_array is not None:
            feature = feature_extractor.predict(img_array)
            features.append(feature.flatten())
            valid_paths.append(path)

    return np.array(features), valid_paths


def normalize_and_compute_similarity(query_feature, database_features):
    query_norm = query_feature / np.linalg.norm(query_feature)
    db_norm = database_features / np.linalg.norm(database_features, axis=1, keepdims=True)
    return np.dot(db_norm, query_norm)


def get_image_paths(directory, max_images=-1):
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(os.path.join(directory, f"*{ext}")))

    if max_images > 0 and len(image_paths) > max_images:
        image_paths = image_paths[:max_images]

    return image_paths


def find_similar_images(target_path, database_dir, top_k=5, max_images=-1):
    image_paths = get_image_paths(database_dir, max_images)

    if not image_paths:
        raise ValueError("No database images found")

    features, valid_paths = extract_features(image_paths)

    query_array = preprocess_image(target_path)
    if query_array is None:
        raise ValueError(f"Cannot process target image: {target_path}")

    query_feature = feature_extractor.predict(query_array).flatten()
    similarities = normalize_and_compute_similarity(query_feature, features)
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            'path': valid_paths[idx],
            'similarity': similarities[idx]
        })

    return results


def create_results_visualization(target_path, results, result_folder):
    target_name = os.path.basename(target_path)
    plt.figure(figsize=(15, 8))

    for i, result in enumerate(results):
        plt.subplot(1, 5, i + 1)
        plt.imshow(plt.imread(result['path']))

        file_name = os.path.basename(result['path'])
        plt.title(f"{i + 1}. Similarity: {result['similarity']:.4f}\n{file_name[:15]}")
        plt.axis('off')

    plt.tight_layout()
    result_path = os.path.join(result_folder, f"similar_images_{target_name}.jpg")
    plt.savefig(result_path, dpi=150, bbox_inches='tight')
    plt.close()

    return result_path


def process_target_image(target_path, result_folder):
    try:
        results = find_similar_images(
            target_path=target_path,
            database_dir=DATABASE_IMAGES_DIR,
            top_k=5
        )

        create_results_visualization(target_path, results, result_folder)
        return None

    except Exception:
        return None


def main():
    target_images = get_image_paths(TARGET_IMAGES_DIR)

    if not target_images:
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    timestamp_folder = os.path.join(RESULTS_DIR, timestamp)
    os.makedirs(timestamp_folder, exist_ok=True)

    for target_path in target_images:
        process_target_image(target_path, timestamp_folder)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass