from flask import Blueprint, render_template, url_for

menu_bp = Blueprint("menu", __name__)

MENU_SECTIONS = [
    {
        "title": "North Indian",
        "description": "Rich gravies, fresh breads, and comfort classics.",
        "items": [
            {"name": "Paneer Butter Masala", "price": 279, "image": "img/paneer_butter_masala.jpg", "note": "Creamy tomato gravy with soft paneer."},
            {"name": "Chole Bhature", "price": 189, "image": "img/chole_bhature.jpg", "note": "Spiced chickpeas with fluffy bhature."},
            {"name": "Butter Chicken", "price": 329, "image": "img/butter_chicken.jpg", "note": "Classic curry with tender chicken."},
            {"name": "Dal Makhani", "price": 219, "image": "img/dal_makhani.jpg", "note": "Slow-cooked black lentils and butter."},
        ],
    },
    {
        "title": "South Indian",
        "description": "Crisp, light, and full of coconut and spice.",
        "items": [
            {"name": "Masala Dosa", "price": 159, "image": "img/masala_dosa.jpg", "note": "Rice crepe with spiced potato filling."},
            {"name": "Idli Sambar", "price": 129, "image": "img/idli_sambar.jpg", "note": "Steamed idli with warm sambar."},
            {"name": "Uttapam", "price": 149, "image": "img/uttapam.jpg", "note": "Thick pancake with vegetables."},
            {"name": "Curd Rice", "price": 119, "image": "img/curd_rice.jpg", "note": "Comforting rice with yogurt tempering."},
        ],
    },
    {
        "title": "Street Food",
        "description": "Bold flavors from India’s busiest stalls.",
        "items": [
            {"name": "Pav Bhaji", "price": 149, "image": "img/pav_bhaji.jpg", "note": "Spiced veggie mash with butter pav."},
            {"name": "Vada Pav", "price": 79, "image": "img/vada_pav.jpg", "note": "Mumbai’s iconic potato burger."},
            {"name": "Samosa Chaat", "price": 99, "image": "img/samosa_chaat.jpg", "note": "Crunchy samosa topped with chutneys."},
            {"name": "Dahi Puri", "price": 89, "image": "img/dahi_puri.jpg", "note": "Puffed puri with yogurt and spice."},
        ],
    },
    {
        "title": "Biryani & Rice",
        "description": "Fragrant rice dishes layered with spice.",
        "items": [
            {"name": "Hyderabadi Biryani", "price": 349, "image": "img/hyderabadi_biryani.jpg", "note": "Aromatic rice with rich masala."},
            {"name": "Veg Biryani", "price": 219, "image": "img/veg_biryani.jpg", "note": "Mixed vegetables and saffron rice."},
            {"name": "Jeera Rice", "price": 119, "image": "img/jeera_rice.jpg", "note": "Cumin-flavored basmati rice."},
            {"name": "Lemon Rice", "price": 109, "image": "img/lemon_rice.jpg", "note": "Tangy rice with curry leaves."},
        ],
    },
    {
        "title": "Desserts & Drinks",
        "description": "Finish with something sweet or chilled.",
        "items": [
            {"name": "Gulab Jamun", "price": 89, "image": "img/gulab_jamun.jpg", "note": "Soft dumplings soaked in syrup."},
            {"name": "Rasgulla", "price": 99, "image": "img/rasgulla.jpg", "note": "Light spongy cheese sweets."},
            {"name": "Mango Lassi", "price": 129, "image": "img/mango_lassi.jpg", "note": "Creamy yogurt drink with mango."},
            {"name": "Masala Chai", "price": 1, "image": "img/masala_chai.jpg", "note": "Spiced tea brewed the Indian way."},
        ],
    },
]


@menu_bp.route("/menu")
def menu():
    menu_sections = []
    for section in MENU_SECTIONS:
        section_copy = {
            "title": section["title"],
            "description": section["description"],
            "items": [],
        }
        for item in section["items"]:
            item_copy = dict(item)
            item_copy["image_url"] = url_for("static", filename=item["image"])
            section_copy["items"].append(item_copy)
        menu_sections.append(section_copy)

    return render_template("menu.html", menu_sections=menu_sections)
