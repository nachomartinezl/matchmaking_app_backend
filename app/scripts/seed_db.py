import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Configuration ---
# Load environment variables from .env file in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')

# --- Main Seeding Logic ---

def seed_database(supabase: Client, data: dict):
    """
    Seeds the database with questionnaires, questions, and options from a JSON object.
    
    This function is idempotent: it checks if a questionnaire exists before inserting.
    """
    print("Starting database seeding process...")

    for namespace, questionnaires in data.items():
        for q_name, q_details in questionnaires.items():
            
            # --- 1. Insert Questionnaire (if it doesn't exist) ---
            print(f"\nProcessing questionnaire: [{namespace}/{q_name}]")
            
            existing_q = supabase.table('questionnaires') \
                                 .select('id') \
                                 .eq('namespace', namespace) \
                                 .eq('name', q_name) \
                                 .execute()

            questionnaire_id = None
            if existing_q.data:
                questionnaire_id = existing_q.data[0]['id']
                print(f"-> Questionnaire '{namespace}/{q_name}' already exists with ID: {questionnaire_id}. Checking for questions...")
            else:
                q_insert_response = supabase.table('questionnaires') \
                                            .insert({'namespace': namespace, 'name': q_name}) \
                                            .execute()
                if not q_insert_response.data:
                    print(f"!! Failed to insert questionnaire '{namespace}/{q_name}'. Aborting this questionnaire.")
                    continue
                questionnaire_id = q_insert_response.data[0]['id']
                print(f"-> Created questionnaire with ID: {questionnaire_id}")

            # --- 2. Insert Questions and Options ---
            original_questions_with_options = []
            
            if isinstance(q_details, list):
                for index, q_item in enumerate(q_details):
                    original_questions_with_options.append({
                        'questionnaire_id': questionnaire_id,
                        'question_text': q_item['question'],
                        'position': index + 1,
                        'temp_options': q_item['options'] 
                    })
            else:
                for index, q_text in enumerate(q_details['questions']):
                    original_questions_with_options.append({
                        'questionnaire_id': questionnaire_id,
                        'question_text': q_text,
                        'position': index + 1,
                        'temp_options': q_details.get('scale', {}).get('options', [])
                    })

            if not original_questions_with_options:
                print("-> No questions found for this questionnaire.")
                continue

            # =================================================================
            # === THE FIX IS HERE =============================================
            # =================================================================
            # Create a 'clean' list of dictionaries to send to the database,
            # removing the 'temp_options' key which does not exist in the DB table.
            questions_for_db = [
                {k: v for k, v in q.items() if k != 'temp_options'} 
                for q in original_questions_with_options
            ]
            
            print(f"-> Preparing to insert {len(questions_for_db)} questions...")
            q_insert_response = supabase.table('questions') \
                                        .insert(questions_for_db) \
                                        .execute()
            
            if not q_insert_response.data:
                print("!! Failed to insert questions. Aborting options for this questionnaire.")
                # You might want to delete the questionnaire created earlier for a clean state
                # supabase.table('questionnaires').delete().eq('id', questionnaire_id).execute()
                continue
            
            print(f"-> Successfully inserted {len(q_insert_response.data)} questions.")
            
            # --- 3. Insert Options for each question ---
            inserted_questions_from_db = q_insert_response.data
            options_to_insert = []
            
            # Match the original data (with options) to the newly inserted data (with DB IDs)
            # by their order, which is preserved in a bulk insert.
            for original_q, db_q in zip(original_questions_with_options, inserted_questions_from_db):
                question_id = db_q['id']
                options_list = original_q['temp_options']
                for index, option_text in enumerate(options_list):
                    options_to_insert.append({
                        'question_id': question_id,
                        'option_text': str(option_text),
                        'position': index + 1
                    })

            if options_to_insert:
                print(f"-> Preparing to insert {len(options_to_insert)} options...")
                opt_insert_response = supabase.table('options') \
                                              .insert(options_to_insert, count="exact") \
                                              .execute()

                # Using count="exact" gives a `count` property in the response
                if opt_insert_response.count is not None:
                    print(f"-> Successfully inserted {opt_insert_response.count} options.")
                else:
                    print("!! Failed to insert options or count was not returned.")

    print("\n✅ Database seeding process complete!")


if __name__ == "__main__":
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")
    else:
        try:
            supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                question_data = json.load(f)
            seed_database(supabase_client, question_data)
        except Exception as e:
            print(f"An error occurred: {e}")