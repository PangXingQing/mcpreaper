from fuzzywuzzy import fuzz
import os

def load_description_file(file_path):
    file_info_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Split by $$$ character
                    parts = line.split("$$$")
                    if len(parts) == 2:
                        file_info_list.append({
                            'description': parts[0],
                            'file_path': parts[1]
                        })
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    return file_info_list

"""
def fuzzy_multi_search(file_info_list, keywords, threshold=60):

    Multi-keyword fuzzy search function
    Args:
        file_info_list: List of file information dictionaries
        keywords: List of search keywords or space-separated string
        threshold: Minimum match percentage (0-100)
    Returns:
        List of tuples (file_info, score)
 
    if isinstance(keywords, str):
        keywords = keywords.strip().split()
    
    results = []
    for file_info in file_info_list:
        description = file_info['description'].lower()
        filename = os.path.basename(file_info['file_path']).lower()
        
        # Calculate match scores for both description and filename
        total_score = 0
        for keyword in keywords:
            keyword = keyword.lower()
            # Get best match score from description and filename
            desc_score = fuzz.partial_ratio(keyword, description)
            file_score = fuzz.partial_ratio(keyword, filename)
            keyword_score = max(desc_score, file_score)
            total_score += keyword_score
            print(f"\n{keyword} - Description Score: {desc_score}%, Filename Score: {file_score}%")
            print(f"\nfilename: {filename} - Description: {description}")
            print(f"\ntotal_score: {total_score}%, keyword_score: {keyword_score}%")
        
        # Average score across all keywords
        avg_score = total_score / len(keywords)
        print(f"\nAverage score for {file_info['description']}: {avg_score}%")
        if avg_score >= threshold:
            results.append((file_info, avg_score))
    
    # Sort by score in descending order
    return sorted(results, key=lambda x: x[1], reverse=True)

def main():
    description_file_path = "C:\\Users\\PXQ\\Desktop\\mcpreaper\\resource\\description.txt"
    file_info_list = load_description_file(description_file_path)
    
    while True:
        search_input = input("Enter search keywords (or 'q' to quit): ")
        if search_input.lower() == 'q':
            break
            
        results = fuzzy_multi_search(file_info_list, search_input)
        
        if not results:
            print("\nNo matches found.")
            continue
            
        print("\nSearch Results:")
        for file_info, score in results:
            print(f"\nMatch Score: {score:.1f}%")
            print(f"Description: {file_info['description']}")
            print(f"File: {file_info['file_path']}")
            print("-" * 50)

if __name__ == "__main__":
    main()
"""