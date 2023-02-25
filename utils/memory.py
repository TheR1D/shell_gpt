from utils.hugging_face import hugging_face_api

def filter_facts(query, all_facts, filter="hf", hf_api_key=None, MAX_FACTS=50):
    if filter == "nofilter":
        return all_facts
    elif filter == "hf":
        #split all facts into lines
        all_facts = all_facts.splitlines()
        #the date is the first two words of a line
        all_facts_without_dates = [fact.split(" ", 2)[2] for fact in all_facts]
        print(all_facts_without_dates)
        
        huggingface_request_json =  {
            "source_sentence": query,
            "sentences": all_facts_without_dates
        }

        response = hugging_face_api(huggingface_request_json, model='sentence_translation', api_key=hf_api_key)

        response_fact_pairs = list(zip(response, all_facts))
        response_fact_pairs.sort(reverse=True)
        response_fact_pairs = response_fact_pairs[:MAX_FACTS]

        #merge all response_fact_pairs onto one string
        # filtered_facts = ""
        # for i, fact_without_date in enumerate(all_facts_without_dates):
        #     if fact_without_date in 
        #     filtered_facts += pair[i] + "\n"


        return all_facts

        # return hugging_face_api(fact, hf_api_key)

