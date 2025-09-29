import pandas as pd
import string
import random
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score

# -----------------------
# Preprocess function
# -----------------------
def preprocess_extension(ext):
    if pd.isna(ext):   # ✅ handle NaN safely
        return "UNKNOWN"
    ext = str(ext).strip().lower()
    if ext == "":
        return "UNKNOWN"
    return ext

# -----------------------
# Load dataset
# -----------------------
df = pd.read_csv("training_data.csv")

# Clean extension column
df["extension"] = df["extension"].apply(preprocess_extension)

# Features and labels
X = df["extension"]   # extensions as input
y = df["category"]    # categories as output

# -----------------------
# Vectorize (Bag of Words)
# -----------------------
vectorizer = CountVectorizer()
X_vec = vectorizer.fit_transform(X)

# -----------------------
# Train-test split
# -----------------------
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42, stratify=y
)

# -----------------------
# Train Naive Bayes Model
# -----------------------
model = MultinomialNB()
model.fit(X_train, y_train)

# -----------------------
# Evaluation
# -----------------------
y_pred = model.predict(X_test)

print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))

# -----------------------
# Save Model + Vectorizer (optional)
# -----------------------
import joblib
joblib.dump(model, "file_classifier_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
print("\n🎉 Model training complete and saved!")
