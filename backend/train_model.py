import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

# 1. Configuration Paths
DATA_DIR = os.path.join("..", "data", "gestures")
DATA_PATH = os.path.join(DATA_DIR, "medical_landmarks_v2.npy")
MODEL_OUTPUT_PATH = os.path.join(DATA_DIR, "signbridge_lstm_model.keras")
LABELS_OUTPUT_PATH = os.path.join(DATA_DIR, "labels.npy")

SEQUENCE_LENGTH = 30
NUM_LANDMARKS = 63

def augment_sequence(seq):
    seq = np.array(seq, dtype=np.float32)
    variants = []

    # Keep only 5 most impactful augmentations
    variants.append(seq.copy())                          # 1. Original
    
    noise = np.random.normal(0, 0.015, seq.shape)
    variants.append(seq + noise)                         # 2. Noise
    
    mirrored = seq.copy()
    mirrored[:, 0::3] = 1.0 - mirrored[:, 0::3]
    variants.append(mirrored)                            # 3. Mirror (left hand)
    
    variants.append(time_warp(seq, factor=1.15))         # 4. Slow motion
    
    variants.append(time_warp(seq, factor=0.85))         # 5. Fast motion

    return variants


def time_warp(seq, factor):
    """
    Stretch or compress a sequence in time, then resample
    back to SEQUENCE_LENGTH frames using linear interpolation.
    factor > 1 = slower (stretched), factor < 1 = faster (compressed)
    """
    original_len = seq.shape[0]
    new_len = max(5, int(original_len * factor))

    # Resample to new_len first
    old_indices = np.linspace(0, original_len - 1, new_len)
    warped = np.zeros((new_len, seq.shape[1]), dtype=np.float32)
    for i in range(seq.shape[1]):
        warped[:, i] = np.interp(old_indices, np.arange(original_len), seq[:, i])

    # Resample back to fixed SEQUENCE_LENGTH
    final_indices = np.linspace(0, new_len - 1, SEQUENCE_LENGTH)
    final = np.zeros((SEQUENCE_LENGTH, seq.shape[1]), dtype=np.float32)
    for i in range(seq.shape[1]):
        final[:, i] = np.interp(final_indices, np.arange(new_len), warped[:, i])

    return final


def rotate_landmarks(seq, max_angle_deg=10):
    """
    Apply a small random rotation to x,y coordinates
    (simulates slightly different camera angle)
    """
    angle = np.radians(np.random.uniform(-max_angle_deg, max_angle_deg))
    cos_a, sin_a = np.cos(angle), np.sin(angle)

    rotated = seq.copy()
    x = seq[:, 0::3] - 0.5  # center around origin
    y = seq[:, 1::3] - 0.5

    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a

    rotated[:, 0::3] = new_x + 0.5
    rotated[:, 1::3] = new_y + 0.5

    return rotated


def load_and_preprocess_data():
    print("🔄 Loading landmark dataset matrix...")
    raw_data = np.load(DATA_PATH, allow_pickle=True).item()

    words = sorted(list(raw_data.keys()))
    word_to_index = {word: idx for idx, word in enumerate(words)}
    np.save(LABELS_OUTPUT_PATH, words)

    # ── STEP 1: Split ORIGINAL videos into train/test FIRST ──
    # This prevents data leakage — augmented copies of the same
    # original video will never cross between train and test sets
    train_originals = []  # (sequence, label_idx)
    test_originals = []

    for word, sequences in raw_data.items():
        label_idx = word_to_index[word]
        seqs = list(sequences)

        if len(seqs) < 2:
            # Too few samples to split — put the only one in train
            train_originals.append((seqs[0], label_idx))
            continue

        # 80/20 split on the ORIGINAL videos only
        train_seqs, test_seqs = train_test_split(
            seqs, test_size=0.2, random_state=42
        )

        for s in train_seqs:
            train_originals.append((s, label_idx))
        for s in test_seqs:
            test_originals.append((s, label_idx))

    print(f"📊 Original videos — Train: {len(train_originals)}, Test: {len(test_originals)}")

    # ── STEP 2: Augment ONLY the training set ──
    X_train, y_train = [], []
    for seq, label_idx in train_originals:
        variants = augment_sequence(seq)
        for v in variants:
            X_train.append(v)
            y_train.append(label_idx)

    # ── STEP 3: Test set stays UNAUGMENTED (real-world evaluation) ──
    X_test, y_test = [], []
    for seq, label_idx in test_originals:
        X_test.append(np.array(seq, dtype=np.float32))
        y_test.append(label_idx)

    X_train = np.array(X_train, dtype=np.float32)
    y_train = np.array(y_train, dtype=np.int32)
    X_test = np.array(X_test, dtype=np.float32)
    y_test = np.array(y_test, dtype=np.int32)

    print(f"📊 After augmentation — Train: {X_train.shape}, Test (clean): {X_test.shape}")

    y_train_encoded = to_categorical(y_train, num_classes=len(words))
    y_test_encoded = to_categorical(y_test, num_classes=len(words))

    return X_train, X_test, y_train_encoded, y_test_encoded, len(words), words


def build_lstm_model(input_shape, num_classes):
    print("🏗️ Constructing LSTM Neural Network Architecture...")

    model = Sequential([
        Input(shape=input_shape),

        LSTM(128, return_sequences=True, activation='tanh'),
        Dropout(0.5),

        LSTM(64, return_sequences=False, activation='tanh'),
        Dropout(0.5),

        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()
    return model


def train():
    X_train, X_test, y_train, y_test, num_classes, words = load_and_preprocess_data()
    input_shape = (X_train.shape[1], X_train.shape[2])

    model = build_lstm_model(input_shape, num_classes)

    print("\n🚀 Firing up training epochs...")

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=15,
        restore_best_weights=True
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=150,
        batch_size=16,
        callbacks=[early_stop],
        verbose=1
    )

    # ── Per-class evaluation on CLEAN test set ──
    print("\n📋 Per-sign accuracy on clean (unaugmented) test set:")
    predictions = model.predict(X_test, verbose=0)
    pred_labels = np.argmax(predictions, axis=1)
    true_labels = np.argmax(y_test, axis=1)

    for idx, word in enumerate(words):
        mask = true_labels == idx
        if mask.sum() == 0:
            print(f"   {word}: no test samples")
            continue
        correct = (pred_labels[mask] == true_labels[mask]).sum()
        total = mask.sum()
        print(f"   {word}: {correct}/{total} correct ({round(100*correct/total, 1)}%)")

    print(f"\n💾 Saving trained model to: {MODEL_OUTPUT_PATH}")
    model.save(MODEL_OUTPUT_PATH)
    print("🏁 Training Pipeline Complete!")


if __name__ == "__main__":
    train()