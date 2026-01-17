from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.athle_db

def merge_world_events():
    # 1. Récupérer toutes les disciplines uniques des Mondiaux
    # Le champ est "event" dans votre collection world_results
    world_events = db.world_results.distinct("event")
    
    print(f"Analyse de {len(world_events)} disciplines mondiales...")
    
    new_events_count = 0
    
    for event_name in world_events:
        if not event_name: continue
        
        event_name_clean = event_name.strip()
        
        # 2. Vérifier si elle existe déjà (nom exact)
        # Attention : "100m" (JO) est différent de "100 Metres" (Mondiaux)
        exists = db.events.find_one({"event_name": event_name_clean})
        
        if not exists:
            # 3. On crée la nouvelle discipline
            # On essaie de détecter le genre automatiquement
            gender = "Unknown"
            if "women" in event_name_clean.lower(): gender = "Female"
            elif "men" in event_name_clean.lower(): gender = "Male"
            
            new_event = {
                "event_name": event_name_clean,
                "gender_category": gender,
                "source": "World Championships"
            }
            db.events.insert_one(new_event)
            new_events_count += 1
            
    print(f"Terminé ! {new_events_count} nouvelles disciplines ajoutées.")

merge_world_events()