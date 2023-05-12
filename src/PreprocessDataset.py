from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from langdetect import detect
from nltk.stem import PorterStemmer
from greek_stemmer import stemmer
import pandas as pd
import numpy as np
import re
import nltk
# nltk.download('punkt')
# nltk.download('stopwords')

def read_csv_and_return_info(file_path):
    # Read the CSV file and store it in a pandas DataFrame
    df = pd.read_csv(file_path)

    # Get the columns of the dataset
    columns = df.columns

    # Get the size of the dataset (number of rows and columns)
    dataset_size = df.shape
    return df, columns, dataset_size


def search_dataframe(df, column_name, specific_value, specific_columns=None):
    if specific_columns is None:
        specific_columns = []

    # Filter the dataframe based on the specific value in the specified column
    filtered_df = df[df[column_name] == specific_value]

    result_dict = {}

    for column in filtered_df.columns:
        if column in specific_columns:
            result_dict[column] = filtered_df[column].tolist()
        else:
            unique_value = filtered_df[column].unique()
            result_dict[column] = unique_value[0] if len(unique_value) == 1 else unique_value.tolist()

    return result_dict


def preprocess_strings(input_data):
    if isinstance(input_data, str):
        if pd.isnull(input_data):
            return ''
        input_data = re.sub(r'\d', 'X', input_data)
        input_data = ''.join(c for c in input_data if c.isalpha() or c == 'X' or c == ' ')
        input_data = input_data.lower()
        return input_data
    elif isinstance(input_data, (list, np.ndarray)):
        processed_data = []
        for item in input_data:
            if pd.isnull(item):
                processed_data.append('')
            elif isinstance(item, str):
                item = re.sub(r'\d', 'X', item)
                item = ''.join(c for c in item if c.isalpha() or c == 'X' or c == ' ')
                item = item.lower()
                processed_data.append(item)
            else:
                raise TypeError("Input data must be a string or a list/array of strings")
        return processed_data
    else:
        raise TypeError("Input data must be a string or a list/array of strings")
    
    
def remove_stopwords(input_data, language):
    english_stopwords = set(stopwords.words("english"))
    greek_stopwords = set(stopwords.words("greek"))

    def process_text(text):
        if pd.isnull(text):
            return np.nan

        if language == "en":
            stopwords_set = english_stopwords
        elif language == "el":
            stopwords_set = greek_stopwords
        else:
            raise ValueError("Unsupported language detected")

        if isinstance(text, str):
            try:
                words = nltk.word_tokenize(text)
                filtered_words = [
                    word for word in words if word.lower() not in stopwords_set]
                return " ".join(filtered_words)
            except:
                return np.nan
        elif isinstance(text, (int, float)):
            return text
        else:
            raise TypeError("Input data must be a string or a numeric type")

    if isinstance(input_data, str):
        return process_text(input_data)
    elif isinstance(input_data, (list, np.ndarray)):
        return [process_text(text) for text in input_data]
    else:
        raise TypeError("Input data must be a string or a list/array of strings")


def stem_strings(input_data, language):
    english_stemmer = PorterStemmer()

    def stem_string(s):
        words = nltk.word_tokenize(s)

        if language == 'en':
            stemmed_words = [english_stemmer.stem(word).lower() for word in words]
        elif language == 'el':
            stemmed_words = [stemmer.stem_word(word, 'vbg').lower() for word in words]
        else:
            raise ValueError("Unsupported language detected")

        return ' '.join(stemmed_words)

    if isinstance(input_data, str):
        return stem_string(input_data)
    elif isinstance(input_data, list):
        return [stem_string(s) for s in input_data]
    else:
        raise TypeError("Input data must be a string or a list of strings")


def validate_language(dataframe, column_name):
    try:
        language = detect(dataframe[column_name][0])
        return language
    except:
        return 'Unknown language'


def execute_complete_preprocess_workflow(csv_file_path, output_file_path):
    dataframe, columns, size = read_csv_and_return_info(csv_file_path)

    # Setting the conversation columns to be used further down the road.
    conversation_columns = ['Attacker_Helper', 'Victim']

    language = validate_language(dataframe=dataframe, column_name='Attacker_Helper')

    result_data = []

    for conversation_id in dataframe['Conversation_ID'].unique():
        conversation_dictionary = search_dataframe(dataframe, 'Conversation_ID', conversation_id, conversation_columns)

        conversation_data = {}

        for column in columns:
            if column == 'Conversation_ID':
                conversation_data[column] = conversation_id
            elif column in conversation_columns:
                conversation_data[column] = preprocess_strings(conversation_dictionary[column])
                conversation_data[column] = remove_stopwords(conversation_data[column], language)
                conversation_data[column] = stem_strings(conversation_data[column], language)
            else:
                conversation_data[column] = conversation_dictionary[column]

        result_data.append(conversation_data)

    # Convert result_data to a DataFrame
    result_dataframe = pd.DataFrame(result_data, columns=columns)

    # Save the preprocessed DataFrame to a CSV file
    result_dataframe.to_csv(output_file_path, index=False)

    return result_dataframe



if __name__ == '__main__':
    file_path = 'Data/Custom_Datasets/conversation_datasets_GPT.csv'
    output_file_path = 'Data/Preprocessed_Datasets/GPT_dataset_preprocessed.csv'
    resulting_dataframe = execute_complete_preprocess_workflow(file_path, output_file_path=output_file_path)
