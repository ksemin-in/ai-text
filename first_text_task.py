# First program for text
print("This is my first text processing program")


# Store text in a variable
text = "Hello!!!, I am Learning Artificial Intelligence and data Science Course???"

# Convert to lowercase & Remove punctuation marks (basic cleaning)
clean_text = text.lower().replace("!", "").replace(",", "").replace("?", "")
print(clean_text)

# Split into tokens (tokenization)
text = "Hello!!!, I am Learning Gen AI???"
clean = text.lower().replace("!", "").replace(",", "").replace("?", "")
tokens = clean.split()
print(tokens)

# Program: Count number of words in the sentence
text = "I am enjoying Python and text processing"
words = text.split()
print("Words:", words)
print("Word count:", len(words))

# Program: Count how many times each word appears
text = "python is good and python is fun"
words = text.split()
frequency = {}

for w in words:
    if w in frequency:
        frequency[w] += 1
    else:
        frequency[w] = 1

print(frequency)

# Remove Numbers
import re
text = "I scored 95 marks in exam and 100 in maths"
clean = re.sub(r'\d+', '', text)
print(clean)

# Remove Extra Spaces
text = "Hello     I    am     learning   python"
clean = " ".join(text.split())
print(clean)

# Remove Stopwords
text = "I am learning python for text processing"
stopwords = ["am", "for", "and", "is", "the", "in"]
tokens = text.split()
clean = [w for w in tokens if w not in stopwords]
print(clean)

# Reverse The Words
text = "I am learning java"
words = text.split()
reverse = words[::-1]
print(reverse)

# Reverse Each letter
text = "text processing module"
letters = text.split()
reverse_letters = [l[::-1] for l in letters]
print(reverse_letters)

# Count Vowels
text = "learning calisthenics"
vowels = "aeiou"
count = sum(1 for c in text if c in vowels)
print("Vowel count:", count)


# Check Palindrome Words
text = "level"
if text == text[::-1]:
    print("Palindrome")
else:
    print("Not palindrome")


# Extract Unique Words
text = "python is fun and python is powerful"
words = text.split()

unique = []

for w in words:
    if words.count(w) == 1:
        unique.append(w)

print("Unique words:", unique)




