import os

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
#from langchain.chains.llm import LLMChain
#from langchain.document_loaders import WebBaseLoader
#from langchain.chains.combine_documents.stuff import StuffDocumentsChain
#from langchain.output_parsers import StructuredOutputParser, ResponseSchema

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']


def generate_tweet_title(text):
    prompt_template = '''
    Here is the content of a tweet that I have bookmarked. I want to generate a title for it that would make me recall what the full tweet was about. 
    Please create this title.
    {tweet_content}
    '''
    prompt = PromptTemplate(template=prompt_template, input_variables=['tweet_content'])
    llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    logging.debug("Tweet title: just before calling AI")
    _input = prompt.format(tweet_content = text)
    return clean_title(llm(_input))

# For some reason the title comes out with extra quotes, double-quotes or /n at the beginning or end. So I need to clean it.
def clean_title(s):
    while s and any(s.startswith(char) or s.endswith(char) for char in ["\n", "'", "\"", " "]):
        s = s.strip("\n '\"")
    return s

'''
def get_article_data(url):
    loader = WebBaseLoader(url)

    # Define prompt
    prompt_template = """
    You are a helpful assistant that curates resources of interest for a human reader. 
    Given the html code of a webpage that contains an article, you try to identify the author of the article, you create a title and a summary for that article. 

    For the author, if you can't identify it with confidence, you can use the name of the publication. If you can't identify the name of the publication, you can return "Unidentified"

    For the title, if the article already has a title, you may use it if you think it is a good one. Be specific. Remove the name of the author from it.

    For the summary, identify the main theses, and organize as bullet points the thought process (no more than a few for each thesis).

    .\n{format_instructions}

    "{text}"
    """

    response_schemas = [
        ResponseSchema(name="title", description="the title of the article"),
        ResponseSchema(name="author", description="the author of the article"),
        ResponseSchema(name="summary", description="the summary of the article")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt = PromptTemplate(
        template=prompt_template, 
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions}
    )

    # Define LLM chain
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", openai_api_key=OPENAI_API_KEY) 
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # Define StuffDocumentsChain
    stuff_chain = StuffDocumentsChain(
        llm_chain=llm_chain, document_variable_name="text"
    )

    docs = loader.load()
    output = stuff_chain.run(docs)
    structured_output = output_parser.parse(output)
    return structured_output['title'], structured_output['author'], structured_output['summary']'''