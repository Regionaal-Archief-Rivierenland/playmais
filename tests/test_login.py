import pytest
import playmais

def test_incorrect_password(page):
    with pytest.raises(RuntimeError):
        with playmais.Playmais() as pm:
            pm.login(page, gebruikersnaam="Incorrect", wachtwoord="Incorrect")
        
    
