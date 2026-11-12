"""Sector definitions shared by sector_pages.py and the home page block (home_info.py).

A sector is a fixed list of HS prefixes chosen by Customs Nepal — not an official classification.
"""

# slug, name, icon, HS prefixes (digits), prefixes to leave out, one-line scope
IMPORT_SECTORS = [
    ('vehicles', 'Vehicles, motorcycles and EVs', '🚗', ['87'], [], 'cars, electric vehicles, motorcycles, buses, trucks, tractors and parts (HS chapter 87)'),
    ('fuel-energy', 'Fuel and energy', '⛽', ['27', '854142', '854143', '8507'], [], 'petrol, diesel, LPG, coal, electricity, solar panels and batteries'),
    ('electronics', 'Electronics and appliances', '📱', ['85', '8471', '8415', '8418', '8450'], ['854142', '854143', '8507'], 'mobile phones, computers, TVs, home appliances and electrical equipment'),
    ('construction-materials', 'Iron, steel and construction materials', '🏗️', ['72', '73', '2523', '69', '6802', '6810', '7003', '7004', '7005', '7007', '7008', '7610'], [], 'iron and steel, cement and clinker, tiles and ceramics, glass and structures'),
    ('pharma-medical', 'Pharmaceuticals and medical equipment', '💊', ['30', '9018', '9019', '9020', '9021', '9022'], [], 'medicines, vaccines and medical, surgical and diagnostic equipment'),
    ('food-edible-oils', 'Food and edible oils', '🌾', ['02', '03', '04', '07', '08', '10', '11', '12', '15', '16', '17', '18', '19', '20', '21'], ['1211'], 'cereals, edible oils, oilseeds, fruit, vegetables, dairy, sugar and prepared foods'),
    ('machinery', 'Machinery and industrial equipment', '⚙️', ['84'], ['8471', '8415', '8418', '8450'], 'industrial, agricultural and construction machinery, engines, pumps and parts'),
    ('textiles-garments', 'Textiles, garments and carpets', '🧵', [str(c) for c in range(50, 64)], [], 'yarn, fabric, readymade garments, carpets, felt and other textile products (HS chapters 50–63)'),
    ('gold-jewellery', 'Gold, silver and jewellery', '🥇', ['71'], [], 'gold, silver, precious stones and jewellery (HS chapter 71)'),
    ('tea-coffee-spices', 'Tea, coffee, spices and herbs', '🍵', ['09', '1211'], [], 'tea, coffee, cardamom, ginger and other spices, and medicinal herbs'),
    ('led-av-lighting', 'LED displays, audio-visual and lighting', '📺', ['8528', '8531', '8524', '8518', '8519', '8521', '8525', '853951', '853952', '9405'], [], 'monitors, projectors and TVs, LED display panels and modules, audio equipment, cameras, LED lamps and light fittings'),
]

# export industries: slug, name, icon, HS prefixes, leave out, scope, /export guide slugs
EXPORT_SECTORS = [
    ('edible-oils-exports', 'Refined edible oils', '🫒', ['1507', '1511', '1512', '1514', '1516', '1517'], [], 'refined soybean, palm, sunflower and other vegetable oils', []),
    ('yarn-fabric-exports', 'Yarn and fabric', '🧶', ['5509', '5402', '5510', '5205', '5206', '5508', '5407', '5512', '5513', '5514', '5515', '5516'], [], 'polyester, acrylic and cotton yarn and woven synthetic fabric', []),
    ('garments-pashmina-exports', 'Readymade garments and pashmina', '👕', ['61', '62'], [], 'knitted and woven clothing, shawls, scarves and pashmina (HS chapters 61 and 62)', ['knitwear', 'pashmina']),
    ('cardamom-spices-exports', 'Cardamom, ginger and spices', '🌿', ['0908', '0910', '0904', '0906', '0907', '0909'], [], 'large cardamom, ginger, turmeric, pepper and other spices', ['cardamom']),
    ('carpets-exports', 'Carpets', '🧵', ['57'], [], 'hand-knotted woollen carpets and other floor coverings (HS chapter 57)', ['carpets']),
    ('jute-exports', 'Jute goods', '🪢', ['53', '6305'], [], 'jute fabric, yarn, twine, sacks and bags', ['jute']),
    ('animal-feed-pet-food-exports', 'Animal feed, oil cake and pet food', '🐕', ['23', '0406'], [], 'oil cake, cattle feed, dog and cat food, and hard cheese (the base of dog chew)', ['dog-chew']),
    ('wood-plywood-exports', 'Plywood, veneer and wood products', '🪵', ['44'], [], 'plywood, veneer sheets and other wood products (HS chapter 44)', []),
    ('juice-noodles-exports', 'Juices, noodles and packaged food', '🧃', ['2009', '2202', '1902', '1905'], [], 'fruit juices and drinks, instant noodles, pasta, biscuits and bakery products', ['noodles']),
    ('felt-handicraft-exports', 'Felt, handicrafts and silver jewellery', '🎨', ['5602', '6504', '6505', '7419', '8306', '7418', '9701', '9703', '7113', '7117', '92'], [], 'felt products, hats, metal statues and craft, paintings, silver jewellery and musical instruments', ['felt']),
    ('iron-steel-exports', 'Iron and steel products', '🔩', ['72', '73'], [], 'galvanised sheet, steel utensils, wire, pipes and other iron and steel goods (HS chapters 72 and 73)', []),
    ('herbs-forest-products-exports', 'Herbs, essential oils and forest products', '🌱', ['1211', '3301', '3806', '3805', '1404', '9603'], [], 'medicinal herbs, essential oils, rosin and turpentine, kattha (catechu) and brooms', ['herbs']),
    ('tea-coffee-exports', 'Tea and coffee', '🍵', ['0902', '0901'], [], 'orthodox and CTC tea and coffee', ['tea']),
    ('footwear-exports', 'Footwear', '👟', ['64'], [], 'sports shoes, sandals and other footwear (HS chapter 64)', []),
    ('cement-clinker-exports', 'Cement and clinker', '🧱', ['2523'], [], 'Portland cement and clinker', []),
]
SECTORS = [s + ([], 'import') for s in [tuple(x) + () for x in IMPORT_SECTORS]] + [tuple(s) + ('export',) for s in EXPORT_SECTORS]


def member(code, pre, exc):
    return any(code.startswith(p) for p in pre) and not any(code.startswith(x) for x in exc)


