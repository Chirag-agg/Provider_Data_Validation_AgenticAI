import json
import os
from crewai.tools import BaseTool
from pydantic import BaseModel
from bs4 import BeautifulSoup


MOCK_DIR = "mock_data"   # root folder for all mock files


# --------------------------------------------------
# 1️⃣ LOAD NPI / DOCTOR REGISTRY TOOL
# --------------------------------------------------

class LoadNPIRegistryTool(BaseTool):
    name: str = "load_npi_registry"
    description: str = "Load mock NPI/doctor registry data from JSON."

    def _run(self) -> dict:
        path = os.path.join(MOCK_DIR, "npi_registry.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# --------------------------------------------------
# 2️⃣ LOAD LICENSE REGISTRY TOOL
# --------------------------------------------------

class LoadLicenseRegistryTool(BaseTool):
    name: str = "load_license_registry"
    description: str = "Load mock medical license registry from JSON."

    def _run(self) -> dict:
        path = os.path.join(MOCK_DIR, "license_registry.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# --------------------------------------------------
# 3️⃣ LOAD HOSPITAL ROSTER TOOL
# --------------------------------------------------

class LoadHospitalRosterTool(BaseTool):
    name: str = "load_hospital_roster"
    description: str = "Load mock hospital roster data from JSON."

    def _run(self) -> dict:
        path = os.path.join(MOCK_DIR, "hospital_roster.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# --------------------------------------------------
# 4️⃣ LOAD GOOGLE MAPS LISTING TOOL
# --------------------------------------------------

class LoadMapsListingTool(BaseTool):
    name: str = "load_maps_listing"
    description: str = "Load mock Google Maps business listings from JSON."

    def _run(self) -> dict:
        path = os.path.join(MOCK_DIR, "maps_listing.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# --------------------------------------------------
# 5️⃣ PARSE CLINIC WEBSITE TOOL (HTML)
# --------------------------------------------------

class LoadClinicWebsiteTool(BaseTool):
    name: str = "load_clinic_website"
    description: str = "Parse mock clinic website HTML and extract doctor info."

    def _run(self) -> list:
        path = os.path.join(MOCK_DIR, "clinic_website.html")

        with open(path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        doctors = []
        for div in soup.find_all("div", class_="doctor"):
            name = div.find("h2").text.strip()

            details = {}
            for p in div.find_all("p"):
                key, value = p.text.split(":", 1)
                details[key.strip().lower()] = value.strip()

            doctors.append({
                "name": name,
                "specialty": details.get("specialty"),
                "phone": details.get("phone"),
                "address": details.get("address"),
                "license_no": details.get("license no")
            })

        return doctors


