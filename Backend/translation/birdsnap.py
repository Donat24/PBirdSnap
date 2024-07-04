from schema.response import BirdSnap, PaginatedResult
from translation.translator import Language, register_translator

de_translation = {
    "acorn-woodpecker":"Eichelspecht",
    "annas-hummingbird":"Annas-Kolibri",
    "blue-jay":"Blauhäher",
    "blue-winged-warbler":"Blauflügelwaldsänger",
    "carolina-chickadee":"Carolina-Meisenhühner",
    "carolina-wren":"Carolina-Zaunkönig",
    "chipping-sparrow":"Chipping-Sperling",
    "common-eider":"Eiderente",
    "common-yellowthroat":"Gelbkehlchen",
    "dark-eyed-junco":"Dunkelaugenjunko",
    "eastern-bluebird":"Ost-Hüttensänger",
    "eastern-towhee":"Ost-Strauß",
    "harris-hawk":"Wüstenbussard",
    "hermit-thrush":"Einsiedlerdrossel",
    "indigo-bunting":"Indigo-Ammer",
    "juniper-titmouse":"Wacholdermeise",
    "northern-cardinal":"Nordkardinal",
    "northern-mockingbird":"Nordspottdrossel",
    "northern-waterthrush":"Nordwasserdrossel",
    "orchard-oriole":"Orchard-Pirol",
    "painted-bunting":"Painted-Burnting",
    "prothonotary-warbler":"Prothonotary-Waldsänger",
    "red-winged-blackbird":"Rotflügelammer",
    "rock-pigeon":"Felsentaube",
    "rofous-crowned-sparrow":"Rotkopfsperling",
    "ruddy-duck":"Ruderente",
    "scarlet-tanager":"Scharlachsperling",
    "snow-goose":"Schneegans",
    "song-sparrow":"Singammer",
    "tufted-titmouse":"Tufted-Titmouse",
    "varied-thrush":"Buntdrossel",
    "white-breasted-nuthatch":"Weißbrustkleiber",
    "white-crowned-sparrow":"Weißkopfsperling",
    "white-throated-sparrow":"Weißkehlsperling",
    "wood-duck":"Waldente",
}

@register_translator(BirdSnap, Language.de)
def translate_birdsnap_de(response : BirdSnap):
    if response.bird_species is not None:
        response.bird_species = [de_translation.get(species, species) for species in response.bird_species]
    return response

@register_translator(PaginatedResult[BirdSnap], Language.de)
def translate_paginated_result_birdsnap_de(response : PaginatedResult[BirdSnap]):
    response.results = [translate_birdsnap_de(birdsnap) for birdsnap in response.results]
    return response