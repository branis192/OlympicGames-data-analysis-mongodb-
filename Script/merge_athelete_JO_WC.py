from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.athle_db

def merge_world_athletes():
    # 1. Récupérer tous les noms uniques des Championnats du Monde
    world_athlete_names = db.world_results.distinct("athlete")
    
    print(f"Analyse de {len(world_athlete_names)} athlètes mondiaux...")
    
    new_athletes_count = 0
    
    for name in world_athlete_names:
        if not name: continue
        
        # 2. Chercher si l'athlète existe déjà dans 'athletes'
        exists = db.athletes.find_one({"name": name.strip()})
        
        if not exists:
            # 3. S'il n'existe pas, on l'ajoute avec des infos par défaut
            # On récupère son pays dans world_results pour l'initialiser
            sample_res = db.world_results.find_one({"athlete": name})
            
            new_athlete = {
                "name": name.strip(),
                "country_origin": sample_res.get("country", "Unknown"),
                "sex": "Unknown", # On ne connaît pas le sexe via world_results directement
                "born": "Unknown",
                "source": "World Championships Only"
            }
            db.athletes.insert_one(new_athlete)
            new_athletes_count += 1
            
    print(f"Fusion terminée ! {new_athletes_count} nouveaux athlètes ajoutés.")

merge_world_athletes()