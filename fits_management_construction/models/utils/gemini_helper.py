# import google.generativeai as gai

# def configure_gemini_api(api_key):
#     """
#     Configure Gemini AI API with the given API key.
#     """
#     gai.configure(api_key=api_key)

# def generate_text(prompt, api_key):
#     """
#     Generate text from Gemini AI based on the given prompt.
#     """
#     configure_gemini_api(api_key)
#     model_instance = gai.GenerativeModel("gemini-pro")
#     generation_config = gai.types.GenerationConfig(
#         candidate_count=1,
#         max_output_tokens=2000,
#     )
#     try:
#         result = model_instance.generate_content(
#             prompt,
#             generation_config=generation_config
#         )
#         return result.text
#     except Exception as e:
#         return f"Error generating text: {e}"
