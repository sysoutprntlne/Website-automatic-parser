from Model.Llama import Model
from prompt.prompting_model import get_prompt

list= ["go out for pizza? and drinks", "Go out for burgers? and fries"]
Model.Llama_model(get_prompt(list, "Clown", "jun.olea1000@gmail.com", "Jun.olea1000@gmail.com", "Bithday party" ))
