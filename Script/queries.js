// Connexion à la base
use("athle_db");

// Q1: Nombre total d'athlètes (uniques)
print("Q1: Nombre total d'athlètes");
print(db.athletes.countDocuments());

// Q2: Nombre de disciplines (épreuves)
print("\nQ2: Nombre de disciplines");
print(db.events.countDocuments());

// Q3: Athlètes ayant gagné une médaille en "Decathlon, Men"
print("\nQ3: Médaillés en Decathlon, Men");
db.results.find(
  { event: "Decathlon, Men", medal: { $ne: "na" } },
  { _id: 0, athlete_name: 1, medal: 1, year: 1, noc: 1 }
).sort({ year: -1 }).forEach(printjson);

// Q4: Nombre d'athlètes féminines avant l'an 2000 (uniques)
print("\nQ4: Athlètes féminines avant 2000");
db.results.aggregate([
  { $match: { sex: "Female", year: { $lt: 2000 } } },
  { $group: { _id: "$athlete_id" } },
  { $count: "total_femmes_avant_2000" }
]).forEach(printjson);

// Q5: Nombre d'athlètes par discipline et par année
print("\nQ5: Athlètes par discipline et par année");
db.results.aggregate([
  {
    $group: {
      _id: { discipline: "$event", annee: "$year" },
      ids: { $addToSet: "$athlete_id" }
    }
  },
  {
    $project: {
      _id: 0,
      discipline: "$_id.discipline",
      annee: "$_id.annee",
      nombre: { $size: "$ids" }
    }
  },
  { $sort: { annee: -1, nombre: -1 } }
]).forEach(printjson);

// Q6: Top 10 des athlètes les plus médaillés
print("\nQ6: Top 10 athlètes les plus médaillés");
db.results.aggregate([
  { $match: { medal: { $ne: "na" } } },
  { $group: { _id: "$athlete_name", total: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
]).forEach(printjson);

// Q7: Nombre d'athlètes par sexe et par pays (uniques)
print("\nQ7: Athlètes par sexe et par pays");
db.results.aggregate([
  {
    $group: {
      _id: { sexe: "$sex", pays: "$noc" },
      ids: { $addToSet: "$athlete_id" }
    }
  },
  {
    $project: {
      _id: 0,
      sexe: "$_id.sexe",
      pays: "$_id.pays",
      nombre: { $size: "$ids" }
    }
  },
  { $sort: { pays: 1 } }
]).forEach(printjson);

// Q8: Disciplines proposées sur moins de 10 éditions
print("\nQ8: Disciplines avec moins de 10 éditions");
db.events.find(
  { nb_editions: { $lt: 10 } },
  { _id: 0, event_name: 1, nb_editions: 1 }
).sort({ nb_editions: 1 }).forEach(printjson);

// Q9: Athlètes les plus médaillés par discipline (ex-aequo)
print("\nQ9: Champions par discipline");
db.results.aggregate([
  { $match: { medal: { $ne: "na" } } },
  {
    $group: {
      _id: { d: "$event", a: "$athlete_name" },
      nb: { $sum: 1 }
    }
  },
  { $sort: { nb: -1 } },
  {
    $group: {
      _id: "$_id.d",
      max: { $max: "$nb" },
      athletes: { $push: { n: "$_id.a", s: "$nb" } }
    }
  },
  {
    $project: {
      _id: 0,
      discipline: "$_id",
      score: "$max",
      champions: {
        $filter: {
          input: "$athletes",
          as: "a",
          cond: { $eq: ["$$a.s", "$max"] }
        }
      }
    }
  }
]).forEach(printjson);

// Q10: Nombre de disciplines par édition
print("\nQ10: Nombre de disciplines par édition");
db.results.aggregate([
  {
    $group: {
      _id: "$year",
      unique_events: { $addToSet: "$event" }
    }
  },
  {
    $project: {
      _id: 0,
      annee: "$_id",
      nb_disciplines: { $size: "$unique_events" }
    }
  },
  { $sort: { annee: -1 } }
]).forEach(printjson);
