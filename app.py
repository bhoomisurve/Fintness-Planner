import os
import numpy as np
import requests
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from googletrans import Translator
import openai
import logging
from PIL import Image
import io
from pathlib import Path
import tensorflow as tf
import time
from PIL import Image
import io
from pathlib import Path
import base64
import time
import re
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import uuid
from flask import redirect, url_for, session, flash
import certifi

try:
    mongo_uri = "MONGO_URI"
    client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=False, tlsCAFile=certifi.where())
    serverSelectionTimeoutMS=60000,  # Wait up to 60 seconds for a server to be found
    connectTimeoutMS=60000,          # Wait up to 60 seconds when establishing the connection
    socketTimeoutMS=60000            # Wait up to 60 seconds for read/write operations
    db = client.farm_assistant
    # Collections
    users = db.users
    posts = db.posts
    comments = db.comments
    disease_info = db.disease_info
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"MongoDB connection error: {e}")





# Configure logging
logging.basicConfig(level=logging.INFO)
UPLOAD_FOLDER = Path('static/uploads')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Configure API keys
genai.configure(api_key="GEMINI_API_KEY")
openai.api_key = "OPENAI_API_KEY"
weather_api_key = 'WEATHER_API_KEY'

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  
CORS(app)

# Initialize translator
translator = Translator()

disease_dic = {
    'Apple___Apple_scab': """ <b>Crop</b>: Apple <br/>Disease: Apple Scab<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Apple scab overwinters primarily in fallen leaves and in the soil. Disease development is favored by wet, cool weather that generally occurs in spring and early summer.

        <br/> 2. Fungal spores are carried by wind, rain or splashing water from the ground to flowers, leaves or fruit. During damp or rainy periods, newly opening apple leaves are extremely susceptible to infection. The longer the leaves remain wet, the more severe the infection will be. Apple scab spreads rapidly between 55-75 degrees Fahrenheit.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Choose resistant varieties when possible.

        <br/>2. Rake under trees and destroy infected leaves to reduce the number of fungal spores available to start the disease cycle over again next spring
        
        <br/>3. Water in the evening or early morning hours (avoid overhead irrigation) to give the leaves time to dry out before infection can occur.
        <br/>4. Spread a 3- to 6-inch layer of compost under trees, keeping it away from the trunk, to cover soil and prevent splash dispersal of the fungal spores.""",

    'Apple___Black_rot': """ <b>Crop</b>: Apple <br/>Disease: Black Rot<br/>
        <br/> Cause of disease:

        <br/><br/>Black rot is caused by the fungus Diplodia seriata (syn Botryosphaeria obtusa).The fungus can infect dead tissue as well as living trunks, branches, leaves and fruits. In wet weather, spores are released from these infections and spread by wind or splashing water. The fungus infects leaves and fruit through natural openings or minor wounds.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Prune out dead or diseased branches.

        <br/>2. Prune out dead or diseased branches.
        
        <br/>3. Remove infected plant material from the area.
        <br/>4. Remove infected plant material from the area.
        <br/>5. Be sure to remove the stumps of any apple trees you cut down. Dead stumps can be a source of spores.""",

    'Apple___Cedar_apple_rust': """ <b>Crop</b>: Apple <br/>Disease: Cedar Apple Rust<br/>
        <br/> Cause of disease:

        <br/><br/>Cedar apple rust (Gymnosporangium juniperi-virginianae) is a fungal disease that depends on two species to spread and develop. It spends a portion of its two-year life cycle on Eastern red cedar (Juniperus virginiana). The pathogen’s spores develop in late fall on the juniper as a reddish brown gall on young branches of the trees.

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Since the juniper galls are the source of the spores that infect the apple trees, cutting them is a sound strategy if there aren’t too many of them.

        <br/>2. While the spores can travel for miles, most of the ones that could infect your tree are within a few hundred feet.
        
        <br/>3. The best way to do this is to prune the branches about 4-6 inches below the galls.""",



    'Apple___healthy': """ <b>Crop</b>: Apple <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",




    'Blueberry___healthy': """ <b>Crop</b>: Blueberry <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",




    'Cherry_(including_sour)___Powdery_mildew': """ <b>Crop</b>: Cherry <br/>Disease: Powdery Mildew<br/>
        <br/> Cause of disease:

        <br/><br/>Podosphaera clandestina, a fungus that most commonly infects young, expanding leaves but can also be found on buds, fruit and fruit stems. It overwinters as small, round, black bodies (chasmothecia) on dead leaves, on the orchard floor, or in tree crotches. Colonies produce more (asexual) spores generally around shuck fall and continue the disease cycle.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Remove and destroy sucker shoots.

        <br/>2. Keep irrigation water off developing fruit and leaves by using irrigation that does not wet the leaves. Also, keep irrigation sets as short as possible.
        
        <br/>3. Follow cultural practices that promote good air circulation, such as pruning, and moderate shoot growth through judicious nitrogen management.""",

    'Cherry_(including_sour)___healthy': """ <b>Crop</b>: Cherry <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': """ <b>Crop</b>: Corn <br/>Disease: Grey Leaf Spot<br/>
        <br/> Cause of disease:

        <br/><br/>Gray leaf spot lesions on corn leaves hinder photosynthetic activity, reducing carbohydrates allocated towards grain fill. The extent to which gray leaf spot damages crop yields can be estimated based on the extent to which leaves are infected relative to grainfill. Damage can be more severe when developing lesions progress past the ear leaf around pollination time.	Because a decrease in functioning leaf area limits photosynthates dedicated towards grainfill, the plant might mobilize more carbohydrates from the stalk to fill kernels.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. In order to best prevent and manage corn grey leaf spot, the overall approach is to reduce the rate of disease growth and expansion.

        <br/>2. This is done by limiting the amount of secondary disease cycles and protecting leaf area from damage until after corn grain formation.
        
        <br/>3. High risk factors for grey leaf spot in corn: <br/>
                    a.	Susceptible hybrid
                    b.	Continuous corn
                    c.	Late planting date
                    d.	Minimum tillage systems
                    e.	Field history of severe disease
                    f.	Early disease activity (before tasseling)
                    g.	Irrigation
                    h.	Favorable weather forecast for disease.""",




    'Corn_(maize)___Common_rust_': """ <b>Crop</b>: Corn(maize) <br/>Disease: Common Rust<br/>
        <br/> Cause of disease:

        <br/><br/>Common corn rust, caused by the fungus Puccinia sorghi, is the most frequently occurring of the two primary rust diseases of corn in the U.S., but it rarely causes significant yield losses in Ohio field (dent) corn. Occasionally field corn, particularly in the southern half of the state, does become severely affected when weather conditions favor the development and spread of rust fungus

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Although rust is frequently found on corn in Ohio, very rarely has there been a need for fungicide applications. This is due to the fact that there are highly resistant field corn hybrids available and most possess some degree of resistance.

        <br/>2. However, popcorn and sweet corn can be quite susceptible. In seasons where considerable rust is present on the lower leaves prior to silking and the weather is unseasonably cool and wet, an early fungicide application may be necessary for effective disease control. Numerous fungicides are available for rust control. """,


    'Corn_(maize)___Northern_Leaf_Blight': """ <b>Crop</b>: Corn(maize) <br/>Disease: Northern Leaf Blight
        <br/>
        <br/> Cause of disease:

        <br/><br/>Northern corn leaf blight (NCLB) is a foliar disease of corn (maize) caused by Exserohilum turcicum, the anamorph of the ascomycete Setosphaeria turcica. With its characteristic cigar-shaped lesions, this disease can cause significant yield loss in susceptible corn hybrids.

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Management of NCLB can be achieved primarily by using hybrids with resistance, but because resistance may not be complete or may fail, it is advantageous to utilize an integrated approach with different cropping practices and fungicides.

        <br/>2. Scouting fields and monitoring local conditions is vital to control this disease.""",


    'Grape___Black_rot': """ <b>Crop</b>: Grape <br/>Disease: Black Rot<br/>
        <br/> Cause of disease:

        <br/><br/> 1. The black rot fungus overwinters in canes, tendrils, and leaves on the grape vine and on the ground. Mummified berries on the ground or those that are still clinging to the vines become the major infection source the following spring.

        <br/> 2. During rain, microscopic spores (ascospores) are shot out of numerous, black fruiting bodies (perithecia) and are carried by air currents to young, expanding leaves. In the presence of moisture, these spores germinate in 36 to 48 hours and eventually penetrate the leaves and fruit stems. 

        <br/> 3. The infection becomes visible after 8 to 25 days. When the weather is wet, spores can be released the entire spring and summer providing continuous infection.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Space vines properly and choose a planting site where the vines will be exposed to full sun and good air circulation. Keep the vines off the ground and insure they are properly tied, limiting the amount of time the vines remain wet thus reducing infection.

        <br/>2. Keep the fruit planting and surrounding areas free of weeds and tall grass. This practice will promote lower relative humidity and rapid drying of vines and thereby limit fungal infection.
        
        <br/>3. Use protective fungicide sprays. Pesticides registered to protect the developing new growth include copper, captan, ferbam, mancozeb, maneb, triadimefon, and ziram. Important spraying times are as new shoots are 2 to 4 inches long, and again when they are 10 to 15 inches long, just before bloom, just after bloom, and when the fruit has set.""",

    'Corn_(maize)___healthy': """ <b>Crop</b>: Corn(maize) <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Grape___Esca_(Black_Measles)': """ <b>Crop</b>: Grape <br/>Disease: Black Measles<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Black Measles is caused by a complex of fungi that includes several species of Phaeoacremonium, primarily by P. aleophilum (currently known by the name of its sexual stage, Togninia minima), and by Phaeomoniella chlamydospora.

        <br/> 2. The overwintering structures that produce spores (perithecia or pycnidia, depending on the pathogen) are embedded in diseased woody parts of vines. The overwintering structures that produce spores (perithecia or pycnidia, depending on the pathogen) are embedded in diseased woody parts of vines.

        <br/> 3. During fall to spring rainfall, spores are released and wounds made by dormant pruning provide infection sites.

        <br/> 4. Wounds may remain susceptible to infection for several weeks after pruning with susceptibility declining over time.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Post-infection practices (sanitation and vine surgery) for use in diseased, mature vineyards are not as effective and are far more costly than adopting preventative practices (delayed pruning, double pruning, and applications of pruning-wound protectants) in young vineyards. 


        <br/>2. Sanitation and vine surgery may help maintain yields. In spring, look for dead spurs or for stunted shoots. Later in summer, when there is a reduced chance of rainfall, practice good sanitation by cutting off these cankered portions of the vine beyond the canker, to where wood appears healthy. Then remove diseased, woody debris from the vineyard and destroy it.
        
        <br/>3. The fungicides labeled as pruning-wound protectants, consider using alternative materials, such as a wound sealant with 5 percent boric acid in acrylic paint (Tech-Gro B-Lock), which is effective against Eutypa dieback and Esca, or an essential oil (Safecoat VitiSeal).""",

    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': """ <b>Crop</b>: Grape <br/>Disease: Leaf Blight<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Apple scab overwinters primarily in fallen leaves and in the soil. Disease development is favored by wet, cool weather that generally occurs in spring and early summer.

        <br/> 2. Fungal spores are carried by wind, rain or splashing water from the ground to flowers, leaves or fruit. During damp or rainy periods, newly opening apple leaves are extremely susceptible to infection. The longer the leaves remain wet, the more severe the infection will be. Apple scab spreads rapidly between 55-75 degrees Fahrenheit.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Choose resistant varieties when possible.

        <br/>2. Rake under trees and destroy infected leaves to reduce the number of fungal spores available to start the disease cycle over again next spring
        
        <br/>3. Water in the evening or early morning hours (avoid overhead irrigation) to give the leaves time to dry out before infection can occur.
        <br/>4. Spread a 3- to 6-inch layer of compost under trees, keeping it away from the trunk, to cover soil and prevent splash dispersal of the fungal spores.""",

    'Grape___healthy': """ <b>Crop</b>: Grape <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Corn_(maize)___healthy': """ <b>Crop</b>: Corn(maize) <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': """<b> Crop</b> : Grape <br/> Disease: Leaf Spot""",


    'Orange___Haunglongbing_(Citrus_greening)': """ <b>Crop</b>: Orange <br/>Disease: Citrus Greening<br/>
        <br/> Cause of disease:

        <br/><br/>  Huanglongbing (HLB) or citrus greening is the most severe citrus disease, currently devastating the citrus industry worldwide. The presumed causal bacterial agent Candidatus Liberibacter spp. affects tree health as well as fruit development, ripening and quality of citrus fruits and juice.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. In regions where disease incidence is low, the most common practices are avoiding the spread of infection by removal of symptomatic trees, protecting grove edges through intensive monitoring, use of pesticides, and biological control of the vector ACP.

        <br/>2. According to Singerman and Useche (2016), CHMAs coordinate insecticide application to control the ACP spreading across area-wide neighboring commercial citrus groves as part of a plan to address the HLB disease.
        
        <br/>3. In addition to foliar nutritional sprays, plant growth regulators were tested, unsuccessfully, to reduce HLB-associated fruit drop (Albrigo and Stover, 2015).""",



    'Peach___Bacterial_spot': """ <b>Crop</b>: Peach <br/>Disease: Bacterial Spot<br/>
        <br/> Cause of disease:

        <br/><br/> 1. The disease is caused by four species of Xanthomonas (X. euvesicatoria, X. gardneri, X. perforans, and X. vesicatoria). In North Carolina, X. perforans is the predominant species associated with bacterial spot on tomato and X. euvesicatoria is the predominant species associated with the disease on pepper.

        <br/> 2. All four bacteria are strictly aerobic, gram-negative rods with a long whip-like flagellum (tail) that allows them to move in water, which allows them to invade wet plant tissue and cause infection.


        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. The most effective management strategy is the use of pathogen-free certified seeds and disease-free transplants to prevent the introduction of the pathogen into greenhouses and field production areas. Inspect plants very carefully and reject infected transplants- including your own!

        <br/>2. In transplant production greenhouses, minimize overwatering and handling of seedlings when they are wet.
        
        <br/>3. Trays, benches, tools, and greenhouse structures should be washed and sanitized between seedlings crops.
        <br/>4. Do not spray, tie, harvest, or handle wet plants as that can spread the disease.""",


    'Pepper,_bell___Bacterial_spot': """ <b>Crop</b>: Pepper <br/>Disease: Bacterial Spot<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Bacterial spot is caused by several species of gram-negative bacteria in the genus Xanthomonas.

        <br/> 2. In culture, these bacteria produce yellow, mucoid colonies. A "mass" of bacteria can be observed oozing from a lesion by making a cross-sectional cut through a leaf lesion, placing the tissue in a droplet of water, placing a cover-slip over the sample, and examining it with a microscope (~200X)..
        
        
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. The primary management strategy of bacterial spot begins with use of certified pathogen-free seed and disease-free transplants.

        <br/>2. The bacteria do not survive well once host material has decayed, so crop rotation is recommended. Once the bacteria are introduced into a field or greenhouse, the disease is very difficult to control.
        
        <br/>3. Pepper plants are routinely sprayed with copper-containing bactericides to maintain a "protective" cover on the foliage and fruit.""",

    'Peach___healthy': """ <b>Crop</b>: Peach <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",

    'Pepper,_bell___healthy': """ <b>Crop</b>: Pepper <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Potato___healthy': """ <b>Crop</b>: Potato <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",

    'Raspberry___healthy': """ <b>Crop</b>: Raspberry <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Soybean___healthy': """ <b>Crop</b>: Soyabean <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",

    'Strawberry___healthy': """ <b>Crop</b>: Strawberry <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",

    'Tomato___healthy': """ <b>Crop</b>: Tomato <br/>Disease: No disease<br/>

        <br/><br/> Don't worry. Your crop is healthy. Keep it up !!!""",


    'Potato___Early_blight': """ <b>Crop</b>: Potato <br/>Disease: Early Blight<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Early blight (EB) is a disease of potato caused by the fungus Alternaria solani. It is found wherever potatoes are grown. 

        <br/> 2. The disease primarily affects leaves and stems, but under favorable weather conditions, and if left uncontrolled, can result in considerable defoliation and enhance the chance for tuber infection. Premature defoliation may lead to considerable reduction in yield.

        <br/> 3. Primary infection is difficult to predict since EB is less dependent upon specific weather conditions than late blight.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Plant only diseasefree, certified seed. 

        <br/>2. Follow a complete and regular foliar fungicide spray program.
        
        <br/>3. Practice good killing techniques to lessen tuber infections.
        <br/>4. Allow tubers to mature before digging, dig when vines are dry, not wet, and avoid excessive wounding of potatoes during harvesting and handling.""",


    'Potato___Late_blight': """ <b>Crop</b>: Potato <br/>Disease: Late Blight<br/>

        Late blight is a potentially devastating disease of potato, infecting leaves, stems and fruits of plants. The disease spreads quickly in fields and can result in total crop failure if untreated. Late blight of potato was responsible for the Irish potato famine of the late 1840s.              
        <br/> Cause of disease:

        <br/><br/> 1. Late blight is caused by the oomycete Phytophthora infestans. Oomycetes are fungus-like organisms also called water molds, but they are not true fungi.

        <br/> 2. There are many different strains of P. infestans. These are called clonal lineages and designated by a number code (i.e. US-23). Many clonal lineages affect both tomato and potato, but some lineages are specific to one host or the other.
        <br/> 3. The host range is typically limited to potato and tomato, but hairy nightshade (Solanum physalifolium) is a closely related weed that can readily become infected and may contribute to disease spread. Under ideal conditions, such as a greenhouse, petunia also may become infected.
        
        
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Seed infection is unlikely on commercially prepared tomato seed or on saved seed that has been thoroughly dried.

        <br/>2. Inspect tomato transplants for late blight symptoms prior to purchase and/or planting, as tomato transplants shipped from southern regions may be infected
        
        <br/>3. If infection is found in only a few plants within a field, infected plants should be removed, disced-under, killed with herbicide or flame-killed to avoid spreading through the entire field.""",


    'Squash___Powdery_mildew': """ <b>Crop</b>: Squash <br/>Disease: Powdery mildew<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Powdery mildew infections favor humid conditions with temperatures around 68-81° F

        <br/> 2. In warm, dry conditions, new spores form and easily spread the disease.
        <br/> 3. Symptoms of powdery mildew first appear mid to late summer in Minnesota.  The older leaves are more susceptible and powdery mildew will infect them first.
        <br/> 4. Wind blows spores produced in leaf spots to infect other leaves.
        <br/> 5. Under favorable conditions, powdery mildew can spread very rapidly, often covering all of the leaves.

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Apply fertilizer based on soil test results. Avoid over-applying nitrogen.

        <br/>2. Provide good air movement around plants through proper spacing, staking of plants and weed control.
        
        <br/>3. Once a week, examine five mature leaves for powdery mildew infection. In large plantings, repeat at 10 different locations in the field.
        <br/>4. If susceptible varieties are growing in an area where powdery mildew has resulted in yield loss in the past, fungicide may be necessary.""",


    'Strawberry___Leaf_scorch': """ <b>Crop</b>: Strawberry <br/>Disease: Leaf Scorch<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Scorched strawberry leaves are caused by a fungal infection which affects the foliage of strawberry plantings. The fungus responsible is called Diplocarpon earliana.

        <br/> 2. Strawberries with leaf scorch may first show signs of issue with the development of small purplish blemishes that occur on the topside of leaves.

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Since this fungal pathogen over winters on the fallen leaves of infect plants, proper garden sanitation is key.

        <br/>2. This includes the removal of infected garden debris from the strawberry patch, as well as the frequent establishment of new strawberry transplants.
        
        <br/>3. The avoidance of waterlogged soil and frequent garden cleanup will help to reduce the likelihood of spread of this fungus.""",



    'Tomato___Bacterial_spot': """ <b>Crop</b>: Tomato <br/>Disease: Bacterial Spot<br/>
        <br/> Cause of disease:

        <br/><br/> 1. The disease is caused by four species of Xanthomonas (X. euvesicatoria, X. gardneri, X. perforans, and X. vesicatoria). In North Carolina, X. perforans is the predominant species associated with bacterial spot on tomato and X. euvesicatoria is the predominant species associated with the disease on pepper.

        <br/> 2. All four bacteria are strictly aerobic, gram-negative rods with a long whip-like flagellum (tail) that allows them to move in water, which allows them to invade wet plant tissue and cause infection.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. The most effective management strategy is the use of pathogen-free certified seeds and disease-free transplants to prevent the introduction of the pathogen into greenhouses and field production areas. Inspect plants very carefully and reject infected transplants- including your own!

        <br/>2. In transplant production greenhouses, minimize overwatering and handling of seedlings when they are wet.
        
        <br/>3. Trays, benches, tools, and greenhouse structures should be washed and sanitized between seedlings crops.
        <br/>4. Do not spray, tie, harvest, or handle wet plants as that can spread the disease""",



    'Tomato___Early_blight': """ <b>Crop</b>: Tomato <br/>Disease: Early Blight<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Early blight can be caused by two different closely related fungi, Alternaria tomatophila and Alternaria solani.
        <br/> 2. Alternaria tomatophila is more virulent on tomato than A. solani, so in regions where A. tomatophila is found, it is the primary cause of early blight on tomato. However, if A.tomatophila is absent, A.solani will cause early blight on tomato.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Use pathogen-free seed, or collect seed only from disease-free plants..

        <br/>2. Rotate out of tomatoes and related crops for at least two years.
        
        <br/>3. Control susceptible weeds such as black nightshade and hairy nightshade, and volunteer tomato plants throughout the rotation.
        <br/>4. Fertilize properly to maintain vigorous plant growth. Particularly, do not over-fertilize with potassium and maintain adequate levels of both nitrogen and phosphorus.
        <br/>5. Avoid working in plants when they are wet from rain, irrigation, or dew.
        <br/>6. Use drip irrigation instead of overhead irrigation to keep foliage dry.""",



    'Tomato___Late_blight': """ <b>Crop</b>: Tomato <br/>Disease: Late Blight<br/>

        Late blight is a potentially devastating disease of tomato, infecting leaves, stems and fruits of plants. The disease spreads quickly in fields and can result in total crop failure if untreated.              
        <br/> Cause of disease:

        <br/><br/> 1. Late blight is caused by the oomycete Phytophthora infestans. Oomycetes are fungus-like organisms also called water molds, but they are not true fungi.

        <br/> 2. There are many different strains of P. infestans. These are called clonal lineages and designated by a number code (i.e. US-23). Many clonal lineages affect both tomato and potato, but some lineages are specific to one host or the other.
        <br/> 3. The host range is typically limited to potato and tomato, but hairy nightshade (Solanum physalifolium) is a closely related weed that can readily become infected and may contribute to disease spread. Under ideal conditions, such as a greenhouse, petunia also may become infected.""",



    'Tomato___Leaf_Mold': """ <b>Crop</b>: Tomato <br/>Disease: Leaf Mold<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Leaf mold is caused by the fungus Passalora fulva (previously called Fulvia fulva or Cladosporium fulvum). It is not known to be pathogenic on any plant other than tomato.

        <br/> 2. Leaf spots grow together and turn brown. Leaves wither and die but often remain attached to the plant.
        <br/> 3. Fruit infections start as a smooth black irregular area on the stem end of the fruit. As the disease progresses, the infected area becomes sunken, dry and leathery.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Use drip irrigation and avoid watering foliage.

        <br/>2. Space plants to provide good air movement between rows and individual plants.
        
        <br/>3. Stake, string or prune to increase airflow in and around the plant.
        <br/>4. Sterilize stakes, ties, trellises etc. with 10 percent household bleach or commercial sanitizer.
        <br/>5. Circulate air in greenhouses or tunnels with vents and fans and by rolling up high tunnel sides to reduce humidity around plants.
        <br/>6. Keep night temperatures in greenhouses higher than outside temperatures to avoid dew formation on the foliage.
        <br/>7. Remove crop residue at the end of the season. Burn it or bury it away from tomato production areas.""",


    'Tomato___Septoria_leaf_spot': """ <b>Crop</b>: Tomato <br/>Disease: Leaf Spot<br/>
        <br/> Cause of disease:

        <br/><br/> Septoria leaf spot is caused by a fungus, Septoria lycopersici. It is one of the most destructive diseases of tomato foliage and is particularly severe in areas where wet, humid weather persists for extended periods.

        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Remove diseased leaves.

        <br/>2. Improve air circulation around the plants.
        
        <br/>3. Mulch around the base of the plants
        <br/>4. Do not use overhead watering.
        <br/>5. Use fungicidal sprayes.""",



    'Tomato___Spider_mites Two-spotted_spider_mite': """ <b>Crop</b>: Tomato <br/>Disease: Two-spotted spider mite<br/>
        <br/> Cause of disease:

        <br/><br/> 1. The two-spotted spider mite is the most common mite species that attacks vegetable and fruit crops.

        <br/> 2. They have up to 20 generations per year and are favored by excess nitrogen and dry and dusty conditions.
        <br/> 3. Outbreaks are often caused by the use of broad-spectrum insecticides which interfere with the numerous natural enemies that help to manage mite populations. 
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Avoid early season, broad-spectrum insecticide applications for other pests.

        <br/>2. Do not over-fertilize
        
        <br/>3. Overhead irrigation or prolonged periods of rain can help reduce populations.""",


    'Tomato___Target_Spo': """ <b>Crop</b>: Tomato <br/>Disease: Target Spot<br/>
        <br/> Cause of disease:

        <br/><br/> 1. The fungus causes plants to lose their leaves; it is a major disease. If infection occurs before the fruit has developed, yields are low.

        <br/> 2. This is a common disease on tomato in Pacific island countries. The disease occurs in the screen house and in the field.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Remove a few branches from the lower part of the plants to allow better airflow at the base

        <br/>2. Remove and burn the lower leaves as soon as the disease is seen, especially after the lower fruit trusses have been picked.
        
        <br/>3. Keep plots free from weeds, as some may be hosts of the fungus.
        <br/>4. Do not use overhead irrigation; otherwise, it will create conditions for spore production and infection.""",


    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': """ <b>Crop</b>: Tomato <br/>Disease: Yellow Leaf Curl Virus<br/>
        <br/> Cause of disease:

        <br/><br/> 1. TYLCV is transmitted by the insect vector Bemisia tabaci in a persistent-circulative nonpropagative manner. The virus can be efficiently transmitted during the adult stages.

        <br/> 2. This virus transmission has a short acquisition access period of 15–20 minutes, and latent period of 8–24 hours.
        <br/><br/> How to prevent/cure the disease <br/>
        <br/>1. Currently, the most effective treatments used to control the spread of TYLCV are insecticides and resistant crop varieties.

        <br/>2. The effectiveness of insecticides is not optimal in tropical areas due to whitefly resistance against the insecticides; therefore, insecticides should be alternated or mixed to provide the most effective treatment against virus transmission.
        
        <br/>3. Other methods to control the spread of TYLCV include planting resistant/tolerant lines, crop rotation, and breeding for resistance of TYLCV. As with many other plant viruses, one of the most promising methods to control TYLCV is the production of transgenic tomato plants resistant to TYLCV.""",




    'Tomato___Tomato_mosaic_virus': """ <b>Crop</b>: Tomato <br/>Disease: Mosaic Virus<br/>
        <br/> Cause of disease:

        <br/><br/> 1. Tomato mosaic virus and tobacco mosaic virus can exist for two years in dry soil or leaf debris, but will only persist one month if soil is moist. The viruses can also survive in infected root debris in the soil for up to two years.

        <br/> 2. Seed can be infected and pass the virus to the plant but the disease is usually introduced and spread primarily through human activity. The virus can easily spread between plants on workers' hands, tools, and clothes with normal activities such as plant tying, removing of suckers, and harvest 
        <br/> 3. The virus can even survive the tobacco curing process, and can spread from cigarettes and other tobacco products to plant material handled by workers after a cigarette


        <br/><br/> How to prevent/cure the disease <br/>


        <br/>1. Purchase transplants only from reputable sources. Ask about the sanitation procedures they use to prevent disease.

        <br/>2. Inspect transplants prior to purchase. Choose only transplants showing no clear symptoms.
        
        <br/>3. Avoid planting in fields where tomato root debris is present, as the virus can survive long-term in roots.
        <br/>4. Wash hands with soap and water before and during the handling of plants to reduce potential spread between plants."""

}


# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

class FarmConsultant:
    def __init__(self):
        self.conversation_history = []
        self.context = """
        You are an AI Farm Consultant named Plantie. Your goal is to provide intelligent,
        context-aware agricultural advice. You should:
        - Ask clarifying questions
        - Provide personalized crop recommendations
        - Offer detailed agricultural insights
        - Maintain a friendly and professional tone
        - Focus on sustainable and efficient farming practices
        - keep the conversation short
        Recommended approach:
        1. Start with initial assessment
        2. Ask about farmer's specific goals
        3. Provide tailored recommendations
        4. Offer practical advice and best practices
        """
        self.conversation = genai.GenerativeModel('gemini-2.0-flash').start_chat(history=[])
        self.disease_dictionary = disease_dic
        self.translator = Translator()

    def transcribe_audio(self, audio_file):
        """
        Transcribe audio file using OpenAI Whisper API
        
        Args:
            audio_file (file): Audio file to be transcribed
        
        Returns:
            str: Transcribed text
        """
        try:
            # Use OpenAI's Whisper model to transcribe audio
            transcription = openai.Audio.transcribe(
                file=audio_file,
                model="whisper-1"
            )
            return transcription['text']
        except Exception as e:
            return f"Transcription error: {str(e)}"

    def get_disease_info(self, crop, disease):
        """
        Retrieve disease information for a specific crop and disease
        
        Args:
            crop (str): Name of the crop
            disease (str): Name of the disease
        
        Returns:
            str: Detailed disease information or a message if not found
        """
        key = f"{crop}___{disease}"
        return self.disease_dictionary.get(key, "No specific information available for this disease.")

    def generate_response(self, user_input, target_language='en'):
        try:
            # Detect input language and translate to English if needed
            detected_lang = self.translator.detect(user_input).lang
            if detected_lang != 'en':
                user_input = self.translator.translate(user_input, dest='en').text

            # Check if the user is asking about a specific crop disease
            disease_keywords = ['disease', 'sick', 'infection', 'symptoms']
            
            if any(keyword in user_input.lower() for keyword in disease_keywords):
                # Try to extract crop and disease names
                words = user_input.lower().split()
                potential_crops = [
                    'apple', 'corn', 'grape', 'tomato', 'potato', 
                    'peach', 'orange', 'pepper', 'strawberry', 'squash'
                ]
                
                found_crop = next((crop for crop in potential_crops if crop in words), None)
                found_disease = next((word for word in words if word in ['scab', 'blight', 'rust', 'mildew']), None)
                
                if found_crop and found_disease:
                    disease_info = self.get_disease_info(
                        found_crop.capitalize(), 
                        found_disease.capitalize()
                    )
                    user_input += f"\n\nHere's the specific disease information:\n{disease_info}"
            
            # Use Gemini to generate a context-aware response
            response = self.conversation.send_message(
                f"Context: {self.context}\n\nUser Input: {user_input}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7
                )
            )
            
            # Translate response back to original language if not English
            if detected_lang != 'en':
                response_text = self.translator.translate(response.text, dest=detected_lang).text
            else:
                response_text = response.text

            return response_text
        except Exception as e:
            return f"I apologize, but there was an error processing your request: {str(e)}"

class IndianCropDiseaseRiskAssessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.crop_disease_profiles = {
            'rice': {
                'optimal_temp_range': (20, 35),
                'optimal_humidity_range': (60, 80),
                'high_risk_diseases': [
                    'Bacterial Leaf Blight', 
                    'Rice Blast', 
                    'Sheath Blight'
                ],
                'regions': ['Tamil Nadu', 'West Bengal', 'Andhra Pradesh']
            },
            'wheat': {
                'optimal_temp_range': (10, 25),
                'optimal_humidity_range': (50, 70),
                'high_risk_diseases': [
                    'Rust', 
                    'Powdery Mildew', 
                    'Loose Smut'
                ],
                'regions': ['Punjab', 'Haryana', 'Uttar Pradesh']
            },
            'cotton': {
                'optimal_temp_range': (25, 35),
                'optimal_humidity_range': (50, 65),
                'high_risk_diseases': [
                    'Bacterial Blight', 
                    'Fusarium Wilt', 
                    'Leaf Curl Virus'
                ],
                'regions': ['Gujarat', 'Maharashtra', 'Telangana']
            },
            'sugarcane': {
                'optimal_temp_range': (20, 35),
                'optimal_humidity_range': (60, 75),
                'high_risk_diseases': [
                    'Red Rot', 
                    'Smut', 
                    'Pokkah Boeng'
                ],
                'regions': ['Uttar Pradesh', 'Maharashtra', 'Karnataka']
            },
            'soybean': {
                'optimal_temp_range': (20, 30),
                'optimal_humidity_range': (60, 80),
                'high_risk_diseases': [
                    'Downy Mildew', 
                    'Rust', 
                    'Yellow Mosaic Virus'
                ],
                'regions': ['Madhya Pradesh', 'Maharashtra', 'Rajasthan']
            }
        }

    def fetch_extended_weather_data(self, city):
        """Fetch comprehensive weather data including forecast"""
        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }

        try:
            response = requests.get(base_url, params=params)
            forecast_data = response.json()
            return self._process_forecast_data(forecast_data)
        except Exception as e:
            logging.error(f"Weather data fetch error: {e}")
            return None

    def _process_forecast_data(self, forecast_data):
        """Process 5-day forecast to extract key weather insights"""
        if not forecast_data or 'list' not in forecast_data:
            return None

        temperatures = []
        humidity_levels = []
        precipitation_chances = []

        for entry in forecast_data['list'][:8]:  # First 24 hours
            temperatures.append(entry['main']['temp'])
            humidity_levels.append(entry['main']['humidity'])
            precipitation_chances.append(
                entry.get('pop', 0) * 100  # Probability of precipitation
            )

        return {
            'avg_temperature': np.mean(temperatures),
            'avg_humidity': np.mean(humidity_levels),
            'precipitation_probability': np.mean(precipitation_chances),
            'temperature_variance': np.std(temperatures),
            'humidity_variance': np.std(humidity_levels)
        }

    def assess_crop_disease_risk(self, weather_data, crop_type='rice'):
        """Comprehensive crop disease risk assessment"""
        if not weather_data:
            return {
                'risk_level': 'Unknown',
                'risk_message': 'Unable to assess risk due to insufficient data',
                'recommendation': 'Check local weather conditions'
            }

        crop_profile = self.crop_disease_profiles.get(crop_type, 
                                                      self.crop_disease_profiles['rice'])
        
        # Multi-factor risk calculation
        risk_factors = []

        # Temperature risk
        temp = weather_data['avg_temperature']
        temp_dev = abs(temp - np.mean(crop_profile['optimal_temp_range']))
        temp_risk = temp_dev / 10  # Normalize temperature deviation

        # Humidity risk
        humidity = weather_data['avg_humidity']
        humidity_dev = abs(humidity - np.mean(crop_profile['optimal_humidity_range']))
        humidity_risk = humidity_dev / 20  # Normalize humidity deviation

        # Precipitation risk
        precip_risk = weather_data['precipitation_probability'] / 100

        # Variance risk (indicates unstable conditions)
        temp_variance_risk = weather_data['temperature_variance'] / 5
        humidity_variance_risk = weather_data['humidity_variance'] / 10

        # Composite risk calculation
        total_risk = (
            temp_risk * 0.3 + 
            humidity_risk * 0.3 + 
            precip_risk * 0.2 + 
            temp_variance_risk * 0.1 + 
            humidity_variance_risk * 0.1
        )

        # Risk level determination
        if total_risk < 0.3:
            risk_level = 'Low'
            recommendation = f"Favorable conditions for {crop_type} cultivation. Recommended regions: {', '.join(crop_profile['regions'][:2])}"
        elif total_risk < 0.6:
            risk_level = 'Moderate'
            recommendation = f"Monitor for potential {crop_profile['high_risk_diseases'][0]}. Take preventive measures."
        else:
            risk_level = 'High'
            recommendation = f"High risk of {', '.join(crop_profile['high_risk_diseases'][:2])}. Immediate protective actions required."

        return {
            'risk_level': risk_level,
            'risk_message': f"{risk_level} disease risk for {crop_type}",
            'recommendation': recommendation,
            'detailed_metrics': {
                'temperature': temp,
                'humidity': humidity,
                'precipitation_chance': weather_data['precipitation_probability']
            }
        }


class CloudDiseaseDetector:
    def __init__(self, disease_dictionary):
        self.disease_dictionary = disease_dictionary
        
    def detect_disease(self, image_file):
        """Detect disease from uploaded image using Cloud API"""
        try:
            # Read and process the image
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Save the uploaded image
            timestamp = int(time.time())
            image_path = UPLOAD_FOLDER / f"upload_{timestamp}.jpg"
            image.save(image_path)
            
            # Convert image to base64 for API request
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Use Gemini to analyze the image and identify the disease
            image_prompt = """
            Analyze this plant image and identify any visible disease.
            If the plant appears healthy, state that it's healthy.
            If a disease is present, provide the following information:
            1. Plant/crop type
            2. Disease name (be specific)
            3. Confidence level (low, medium, high)
            
            Format your response exactly like this example:
            CROP: Tomato
            DISEASE: Late Blight
            CONFIDENCE: High
            
            or if healthy:
            CROP: Apple
            DISEASE: Healthy
            CONFIDENCE: High
            """
            
            response = model.generate_content([image_prompt, {"mime_type": "image/jpeg", "data": base64.b64decode(img_str)}])
            analysis_text = response.text
            
            # Parse the response using regex
            crop_match = re.search(r'CROP:\s*(.*)', analysis_text)
            disease_match = re.search(r'DISEASE:\s*(.*)', analysis_text)
            confidence_match = re.search(r'CONFIDENCE:\s*(.*)', analysis_text)
            
            if not all([crop_match, disease_match, confidence_match]):
                return {
                    "success": False,
                    "message": "Could not parse the detection results",
                    "image_path": str(image_path.relative_to(Path('static')))
                }
            
            crop = crop_match.group(1).strip()
            disease = disease_match.group(1).strip()
            confidence_text = confidence_match.group(1).strip()
            
            # Convert text confidence to numeric
            confidence_map = {"Low": 30, "Medium": 60, "High": 90}
            confidence = confidence_map.get(confidence_text, 50)
            
            # Check if plant is healthy
            if disease.lower() == "healthy":
                return {
                    "success": True,
                    "crop": crop,
                    "disease": "Healthy",
                    "confidence": confidence,
                    "image_path": str(image_path.relative_to(Path('static'))),
                    "recommendation": f"Your {crop} plant appears healthy! Continue with good agricultural practices."
                }
            
            # Look up disease info in dictionary
            disease_key = f"{crop}___{disease}"
            disease_info = self.disease_dictionary.get(disease_key)
            
            # If not found, try a fuzzy match
            if not disease_info:
                # Look for partial matches
                for key in self.disease_dictionary:
                    if crop.lower() in key.lower() and disease.lower() in key.lower():
                        disease_key = key
                        disease_info = self.disease_dictionary[key]
                        break
            
            # If still not found, generate recommendation with Gemini
            if not disease_info:
                recommendation_prompt = f"""
                Provide treatment recommendations for {disease} in {crop} plants.
                Include:
                1. Cause of the disease
                2. How to prevent it
                3. How to treat it
                Format as HTML with <br/> tags for line breaks.
                """
                
                recommendation_response = genai.GenerativeModel('gemini-2.0-flash').generate_content(recommendation_prompt)
                disease_info = recommendation_response.text
            
            return {
                "success": True,
                "crop": crop,
                "disease": disease,
                "confidence": confidence,
                "image_path": str(image_path.relative_to(Path('static'))),
                "disease_info": disease_info
            }
            
        except Exception as e:
            logging.error(f"Disease detection error: {e}")
            return {
                "success": False,
                "message": f"Error during disease detection: {str(e)}",
                "image_path": str(image_path.relative_to(Path('static'))) if 'image_path' in locals() else None
            }

class Community:
    @staticmethod
    def create_user(username, email, password, location=None, crops=None):
        """Create a new user in the community"""
        try:
            # Check if user already exists
            if users.find_one({"email": email}):
                return False, "User with this email already exists"
            
            user_id = str(uuid.uuid4())
            user = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password": password,  # In production, use password hashing
                "location": location,
                "crops": crops or [],
                "join_date": datetime.now(),
                "reputation": 0
            }
            users.insert_one(user)
            return True, user_id
        except Exception as e:
            logging.error(f"User creation error: {e}")
            return False, str(e)
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate a user"""
        try:
            user = users.find_one({"email": email, "password": password})
            if user:
                return True, user
            return False, "Invalid credentials"
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False, str(e)
    
    @staticmethod
    def create_post(user_id, title, content, category, image_path=None):
        """Create a new post in the community forum"""
        try:
            post = {
                "user_id": user_id,
                "title": title,
                "content": content,
                "category": category,
                "image_path": image_path,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "likes": 0,
                "comments": []
            }
            result = posts.insert_one(post)
            return True, str(result.inserted_id)
        except Exception as e:
            logging.error(f"Post creation error: {e}")
            return False, str(e)
    
    @staticmethod
    def get_posts(category=None, limit=10, skip=0):
        """Get posts from the community forum"""
        try:
            query = {}
            if category:
                query["category"] = category
                
            pipeline = [
                {"$match": query},
                {"$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$project": {
                    "_id": 1,
                    "title": 1,
                    "content": 1,
                    "category": 1,
                    "image_path": 1,
                    "created_at": 1,
                    "likes": 1,
                    "comment_count": {"$size": {"$ifNull": ["$comments", []]}},
                    "username": "$user.username"
                }},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            
            result = list(posts.aggregate(pipeline))
            return result
        except Exception as e:
            logging.error(f"Get posts error: {e}")
            return []
    
    @staticmethod
    def get_post(post_id):
        """Get a single post with comments"""
        try:
            post = posts.find_one({"_id": ObjectId(post_id)})
            if not post:
                return None
                
            # Get user information
            user = users.find_one({"user_id": post["user_id"]})
            post["username"] = user["username"] if user else "Unknown"
            
            # Get comments
            post_comments = list(comments.find({"post_id": post_id}).sort("created_at", -1))
            for comment in post_comments:
                commenter = users.find_one({"user_id": comment["user_id"]})
                comment["username"] = commenter["username"] if commenter else "Unknown"
            
            post["comments"] = post_comments
            return post
        except Exception as e:
            logging.error(f"Get post error: {e}")
            return None
    
    @staticmethod
    def add_comment(post_id, user_id, content):
        """Add a comment to a post"""
        try:
            comment = {
                "post_id": post_id,
                "user_id": user_id,
                "content": content,
                "created_at": datetime.now(),
                "likes": 0
            }
            result = comments.insert_one(comment)
            
            # Add comment reference to post
            posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"comments": str(result.inserted_id)}}
            )
            
            return True, str(result.inserted_id)
        except Exception as e:
            logging.error(f"Add comment error: {e}")
            return False, str(e)
    
    @staticmethod
    def like_post(post_id, user_id):
        """Like a post"""
        try:
            posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"likes": 1}}
            )
            return True
        except Exception as e:
            logging.error(f"Like post error: {e}")
            return False
    
    @staticmethod
    def import_disease_dictionary(disease_dic):
        """Import disease dictionary to MongoDB"""
        try:
            if disease_info.count_documents({}) == 0:
                entries = []
                for key, value in disease_dic.items():
                    crop, disease = key.split("___")
                    entry = {
                        "key": key,
                        "crop": crop,
                        "disease": disease,
                        "info": value
                    }
                    entries.append(entry)
                
                if entries:
                    disease_info.insert_many(entries)
                return True
            return False  # Data already exists
        except Exception as e:
            logging.error(f"Disease dictionary import error: {e}")
            return False

# Initialize the farm consultant and disease risk assessor
farm_consultant = FarmConsultant()
crop_risk_assessor = IndianCropDiseaseRiskAssessor(weather_api_key)
disease_detector = CloudDiseaseDetector(disease_dic)
community = Community()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/translator')
def translator_page():
    return render_template('translator_consultant.html')

@app.route('/crop-risk')
def crop_risk_page():
    return render_template('india_crop_risk.html')

@app.route('/consult', methods=['POST'])
def consult():
    user_input = request.json.get('message', '').strip()
    target_language = request.json.get('language', 'en')
   
    if not user_input:
        return jsonify({'message': "I'm listening. What would you like to discuss about farming?"})
   
    response = farm_consultant.generate_response(user_input, target_language)
   
    return jsonify({'message': response})

@app.route('/disease-detection')
def disease_detection_page():
    return render_template('disease_detection.html')

@app.route('/crop-disease-risk', methods=['POST'])
def crop_disease_risk():
    data = request.json
    city = data.get('city', 'New Delhi')
    crop_type = data.get('crop', 'rice')
    
    weather_data = crop_risk_assessor.fetch_extended_weather_data(city)
    risk_assessment = crop_risk_assessor.assess_crop_disease_risk(weather_data, crop_type)
    
    return jsonify(risk_assessment)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'})
    
    audio_file = request.files['audio']
    transcription = farm_consultant.transcribe_audio(audio_file)
    
    return jsonify({'transcription': transcription})

@app.route('/detect-disease', methods=['POST'])
def detect_disease():
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No image file provided'
        })
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No image selected'
        })
    
    result = disease_detector.detect_disease(image_file)
    return jsonify(result)



@app.route('/community')
def community_page():
    posts_list = community.get_posts(limit=10)
    return render_template('community.html', posts=posts_list)

@app.route('/community/category/<category>')
def community_category(category):
    posts_list = community.get_posts(category=category, limit=10)
    return render_template('community.html', posts=posts_list, active_category=category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, result = community.authenticate_user(email, password)
        if success:
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            flash('Login successful!')
            return redirect(url_for('community_page'))
        else:
            flash(result)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        location = request.form.get('location')
        crops = request.form.get('crops', '').split(',')
        crops = [crop.strip() for crop in crops if crop.strip()]
        
        success, result = community.create_user(username, email, password, location, crops)
        if success:
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        else:
            flash(result)
            
    return render_template('register.html')

@app.route('/post/<post_id>')
def view_post(post_id):
    post = community.get_post(post_id)
    if not post:
        flash('Post not found')
        return redirect(url_for('community_page'))
    
    return render_template('post.html', post=post)

@app.route('/create-post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        flash('Please log in to create a post')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        image = request.files.get('image')
        
        image_path = None
        if image and image.filename:
            timestamp = int(time.time())
            image_path = f"uploads/community_{timestamp}_{image.filename}"
            image.save(os.path.join(app.static_folder, image_path))
        
        success, result = community.create_post(
            session['user_id'], title, content, category, image_path
        )
        
        if success:
            flash('Post created successfully!')
            return redirect(url_for('community_page'))
        else:
            flash(f'Error creating post: {result}')
    
    return render_template('create_post.html')

@app.route('/add-comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        flash('Please log in to comment')
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    success, result = community.add_comment(post_id, session['user_id'], content)
    
    if success:
        flash('Comment added!')
    else:
        flash(f'Error adding comment: {result}')
    
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/like-post/<post_id>')
def like_post(post_id):
    if 'user_id' not in session:
        flash('Please log in to like posts')
        return redirect(url_for('login'))
    
    community.like_post(post_id, session['user_id'])
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)