import pytest
import playmais

def test_incorrect_password(page):
    with pytest.raises(RuntimeError):
        playmais.login(page, gebruikersnaam="Incorrect", wachtwoord="Incorrect")
        
    
