"""
listing_finder.py
=================
Finds 1000+ business listing / directory websites where you can
submit your business for backlinks and visibility.

Data collected per site:
    - Website Name
    - URL
    - Domain Authority (DA) — via OpenPageRank free API
    - Type: Free / Paid / Freemium
    - Link Type: DoFollow / NoFollow / Mixed
    - Category: Local Directory, Classifieds, Review Site, etc.
    - Country Focus: India, Global, US, etc.
    - Status: Live / Dead

Usage:
    python listing_finder.py                    # Full run (scrape + validate + export)
    python listing_finder.py --skip-validate    # Skip live-check (faster)
    python listing_finder.py --excel            # Also export to Excel
    python listing_finder.py --da               # Fetch Domain Authority (slower)
"""

import os
import re
import sys
import csv
import time
import logging
import argparse
import platform
import subprocess
from datetime import datetime
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ===========================================================
# CONFIG
# ===========================================================

OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "business_listing_sites.csv")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "business_listing_sites.xlsx")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Max threads for concurrent URL validation
MAX_WORKERS = 20
REQUEST_TIMEOUT = 10

# OpenPageRank free API (get key at https://www.domcop.com/openpagerank/auth/signup)
OPENPAGERANK_API_KEY = ""  # Leave empty to skip DA; set your free key to enable

# ===========================================================
# LOGGING
# ===========================================================

def setup_logging():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(OUTPUT_DIR, "listing_finder.log"), encoding="utf-8"),
        ],
    )

logger = logging.getLogger(__name__)


# ===========================================================
# SEED DATABASE — curated list of known listing sites
# ===========================================================

SEED_SITES = [
    # ---- INDIAN LOCAL DIRECTORIES ----
    {"name": "JustDial", "url": "https://www.justdial.com", "category": "Local Directory", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "Sulekha", "url": "https://www.sulekha.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaMART", "url": "https://www.indiamart.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "TradeIndia", "url": "https://www.tradeindia.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "ExportersIndia", "url": "https://www.exportersindia.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndianYellowPages", "url": "https://www.indianyellowpages.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Grotal", "url": "https://www.grotal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "AskLaila", "url": "https://www.asklaila.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Clickindia", "url": "https://www.clickindia.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Fundoodata", "url": "https://www.fundoodata.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Dial India Online", "url": "https://www.dialindiaonline.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "GetIt", "url": "https://www.getit.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Yellow Pages India", "url": "https://www.yellowpages.co.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Shopkhoj", "url": "https://www.shopkhoj.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Kompass India", "url": "https://in.kompass.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Justbaazaar", "url": "https://www.justbaazaar.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaCatalog", "url": "https://www.indiacatalog.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Infoline", "url": "https://www.infoline.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "MyHuckleberry India", "url": "https://www.myhuckleberry.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Yalwa India", "url": "https://www.yalwa.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Tupalo India", "url": "https://www.tupalo.co", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaBizList", "url": "https://www.indiabizlist.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BusinessListings.net.in", "url": "https://www.businesslistings.net.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "VConnect", "url": "https://www.vconnect.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "GoIndustry", "url": "https://www.goindustry.in", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Whodis India", "url": "https://www.whoislab.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "UrbanPro", "url": "https://www.urbanpro.com", "category": "Service Directory", "type": "Freemium", "link_type": "NoFollow", "country": "India"},
    {"name": "Practo", "url": "https://www.practo.com", "category": "Healthcare Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Zomato", "url": "https://www.zomato.com", "category": "Food Directory", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "Swiggy", "url": "https://www.swiggy.com", "category": "Food Directory", "type": "Freemium", "link_type": "NoFollow", "country": "India"},
    {"name": "MagicBricks", "url": "https://www.magicbricks.com", "category": "Real Estate Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "99acres", "url": "https://www.99acres.com", "category": "Real Estate Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "NaukriHub", "url": "https://www.naukrihub.com", "category": "Job Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Quikr", "url": "https://www.quikr.com", "category": "Classifieds", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "OLX India", "url": "https://www.olx.in", "category": "Classifieds", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "DialMe", "url": "https://www.dialme.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "ServicesCreator", "url": "https://www.servicescreator.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "SmartGuy", "url": "https://www.smartguy.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BizMakersIndia", "url": "https://www.bizmakersindia.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaConnect", "url": "https://www.indiaconnect.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaBizClub", "url": "https://www.indiabizclub.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Tradeindia Business Directory", "url": "https://www.tradeindia.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Power2SME", "url": "https://www.power2sme.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Vyapar", "url": "https://www.vyapar.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "BizHat", "url": "https://www.bizhat.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "ConnectIndia", "url": "https://www.connectindia.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "HelpingDoc", "url": "https://www.helpingdoc.com", "category": "Healthcare Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Vcsdata", "url": "https://www.vcsdata.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Indismart", "url": "https://www.indismart.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "SearchIndia", "url": "https://www.searchindia.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "WeBengal", "url": "https://www.webengal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "PuneOnline", "url": "https://www.puneonline.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "HyderabadOnline", "url": "https://www.hyderabadonline.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "KolkataOnline", "url": "https://www.kolkataonline.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "AhmedabadOnline", "url": "https://www.ahmedabadonline.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Jadooz", "url": "https://www.jadooz.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "FindGlocal", "url": "https://www.findglocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "LocalDukaan", "url": "https://www.localdukaan.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "MyBillBook", "url": "https://www.mybillbook.in", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Industrysearch India", "url": "https://www.industrysearch.in", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "FinderMaster", "url": "https://www.findermaster.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BusinessWala", "url": "https://www.businesswala.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Magicpin", "url": "https://www.magicpin.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Cygnet India", "url": "https://www.cygnetindia.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Apnaindia", "url": "https://www.apnaindia.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "LocalFirst", "url": "https://www.localfirst.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BestBizLocal India", "url": "https://www.bestbizlocal.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "SmartBizPages", "url": "https://www.smartbizpages.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Justlocal", "url": "https://www.justlocal.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Elistingz", "url": "https://www.elistingz.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "India Business Directory", "url": "https://www.indiabusinessdirectory.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Biz15", "url": "https://www.biz15.co.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "NextBizThing", "url": "https://www.nextbizthing.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "ZipDial", "url": "https://www.zipdial.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},

    # ---- GLOBAL DIRECTORIES ----
    {"name": "Google Business Profile", "url": "https://business.google.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Bing Places", "url": "https://www.bingplaces.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Apple Maps Connect", "url": "https://mapsconnect.apple.com", "category": "Local Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Yelp", "url": "https://www.yelp.com", "category": "Review Site", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Facebook Business", "url": "https://www.facebook.com/business", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "LinkedIn Company Page", "url": "https://www.linkedin.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Yellow Pages", "url": "https://www.yellowpages.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Foursquare", "url": "https://www.foursquare.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TripAdvisor", "url": "https://www.tripadvisor.com", "category": "Review Site", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "BBB (Better Business Bureau)", "url": "https://www.bbb.org", "category": "Review Site", "type": "Freemium", "link_type": "DoFollow", "country": "US"},
    {"name": "Trustpilot", "url": "https://www.trustpilot.com", "category": "Review Site", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Manta", "url": "https://www.manta.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Hotfrog", "url": "https://www.hotfrog.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Cylex", "url": "https://www.cylex.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Hub.biz", "url": "https://www.hub.biz", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Spoke.com", "url": "https://www.spoke.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Brownbook", "url": "https://www.brownbook.net", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Tuugo", "url": "https://www.tuugo.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Fyple", "url": "https://www.fyple.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Enrollbusiness", "url": "https://www.enrollbusiness.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "EZlocal", "url": "https://www.ezlocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Cybo", "url": "https://www.cybo.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "FindOpen", "url": "https://www.findopen.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "N49", "url": "https://www.n49.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Wand.com", "url": "https://www.wand.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ZipLeaf", "url": "https://www.zipleaf.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "iGlobal", "url": "https://www.iglobal.co", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Storeboard", "url": "https://www.storeboard.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "2FindLocal", "url": "https://www.2findlocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Superpages", "url": "https://www.superpages.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "DexKnows", "url": "https://www.dexknows.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "ChamberofCommerce", "url": "https://www.chamberofcommerce.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "MapQuest", "url": "https://www.mapquest.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "ShowMeLocal", "url": "https://www.showmelocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Local.com", "url": "https://www.local.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Citysearch", "url": "https://www.citysearch.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Merchantcircle", "url": "https://www.merchantcircle.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Alignable", "url": "https://www.alignable.com", "category": "Business Network", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Nextdoor Business", "url": "https://business.nextdoor.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "US"},
    {"name": "Angi (Angie's List)", "url": "https://www.angi.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Thumbtack", "url": "https://www.thumbtack.com", "category": "Service Directory", "type": "Freemium", "link_type": "NoFollow", "country": "US"},
    {"name": "HomeAdvisor", "url": "https://www.homeadvisor.com", "category": "Service Directory", "type": "Paid", "link_type": "DoFollow", "country": "US"},
    {"name": "Bark.com", "url": "https://www.bark.com", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Clutch.co", "url": "https://clutch.co", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GoodFirms", "url": "https://www.goodfirms.co", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "G2", "url": "https://www.g2.com", "category": "Review Site", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Capterra", "url": "https://www.capterra.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GetApp", "url": "https://www.getapp.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Software Advice", "url": "https://www.softwareadvice.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Crunchbase", "url": "https://www.crunchbase.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "AngelList", "url": "https://angel.co", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ProductHunt", "url": "https://www.producthunt.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BetaList", "url": "https://betalist.com", "category": "Startup Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "SaaSHub", "url": "https://www.saashub.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AlternativeTo", "url": "https://alternativeto.net", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SourceForge", "url": "https://sourceforge.net", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Glassdoor", "url": "https://www.glassdoor.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Indeed Company Pages", "url": "https://www.indeed.com", "category": "Job Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Zillow", "url": "https://www.zillow.com", "category": "Real Estate Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Houzz", "url": "https://www.houzz.com", "category": "Home Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Avvo", "url": "https://www.avvo.com", "category": "Legal Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Healthgrades", "url": "https://www.healthgrades.com", "category": "Healthcare Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Zocdoc", "url": "https://www.zocdoc.com", "category": "Healthcare Directory", "type": "Freemium", "link_type": "DoFollow", "country": "US"},
    {"name": "Vitals.com", "url": "https://www.vitals.com", "category": "Healthcare Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "FindLaw", "url": "https://www.findlaw.com", "category": "Legal Directory", "type": "Paid", "link_type": "DoFollow", "country": "US"},
    {"name": "Lawyers.com", "url": "https://www.lawyers.com", "category": "Legal Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Thumbtack", "url": "https://www.thumbtack.com", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "US"},
    {"name": "Bark", "url": "https://www.bark.com", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Expertise.com", "url": "https://www.expertise.com", "category": "Service Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Birdeye", "url": "https://birdeye.com", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "ThomasNet", "url": "https://www.thomasnet.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Europages", "url": "https://www.europages.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Europe"},
    {"name": "Kompass", "url": "https://www.kompass.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- FREE DIRECTORY SUBMISSION SITES ----
    {"name": "FreeListingIndia", "url": "https://www.freelistingindia.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "LocalBizNetwork", "url": "https://www.localbiznetwork.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Spoke", "url": "https://www.spoke.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Salespider", "url": "https://www.salespider.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Nexdu", "url": "https://www.nexdu.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Bizvotes", "url": "https://www.bizvotes.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "MyLocalServices", "url": "https://www.mylocalservices.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "StartLocal", "url": "https://www.startlocal.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "Opendi", "url": "https://www.opendi.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Bizexposed", "url": "https://www.bizexposed.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Lacartes", "url": "https://www.lacartes.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Entireweb", "url": "https://www.entireweb.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Jayde", "url": "https://www.jayde.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Chamberrate", "url": "https://www.chamberrate.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "1800Dentist", "url": "https://www.1800dentist.com", "category": "Healthcare Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Dentist.com", "url": "https://www.dentist.com", "category": "Healthcare Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Freelistingusa", "url": "https://www.freelistingusa.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Citysquares", "url": "https://www.citysquares.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Golocal247", "url": "https://www.golocal247.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Punchbowl", "url": "https://www.punchbowl.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},

    # ---- SOCIAL / PROFILE / CITATION SITES ----
    {"name": "Twitter/X Business", "url": "https://www.twitter.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Instagram Business", "url": "https://www.instagram.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Pinterest Business", "url": "https://www.pinterest.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "YouTube Channel", "url": "https://www.youtube.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Reddit", "url": "https://www.reddit.com", "category": "Social Directory", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Medium", "url": "https://www.medium.com", "category": "Content Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Quora", "url": "https://www.quora.com", "category": "Q&A Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "SlideShare", "url": "https://www.slideshare.net", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "About.me", "url": "https://about.me", "category": "Profile Site", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Gravatar", "url": "https://gravatar.com", "category": "Profile Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "WordPress.com", "url": "https://wordpress.com", "category": "Content Platform", "type": "Freemium", "link_type": "NoFollow", "country": "Global"},
    {"name": "Blogger", "url": "https://www.blogger.com", "category": "Content Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Tumblr", "url": "https://www.tumblr.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Weebly", "url": "https://www.weebly.com", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Wix", "url": "https://www.wix.com", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Sites.Google.com", "url": "https://sites.google.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Issuu", "url": "https://issuu.com", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Behance", "url": "https://www.behance.net", "category": "Portfolio Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Dribbble", "url": "https://dribbble.com", "category": "Portfolio Site", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "GitHub", "url": "https://github.com", "category": "Developer Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "GitLab", "url": "https://gitlab.com", "category": "Developer Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Disqus", "url": "https://disqus.com", "category": "Profile Site", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Livejournal", "url": "https://www.livejournal.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- CLASSIFIEDS SITES ----
    {"name": "Craigslist", "url": "https://www.craigslist.org", "category": "Classifieds", "type": "Free", "link_type": "NoFollow", "country": "US"},
    {"name": "Gumtree", "url": "https://www.gumtree.com", "category": "Classifieds", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "LocantoBD", "url": "https://www.locanto.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Adpost", "url": "https://www.adpost.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ClassifiedsForFree", "url": "https://www.classifiedsforfree.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "USFreeAds", "url": "https://www.usfreeads.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Oodle", "url": "https://www.oodle.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Hoobly", "url": "https://www.hoobly.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Pennysaver", "url": "https://www.pennysaverusa.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Geebo", "url": "https://www.geebo.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Backpage Alternatives", "url": "https://www.bedpage.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},

    # ---- WEB / GENERAL DIRECTORIES ----
    {"name": "DMOZ (Curlie)", "url": "https://curlie.org", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Best of the Web", "url": "https://botw.org", "category": "Web Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "JoeAnt", "url": "https://www.joeant.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SoMuch", "url": "https://www.somuch.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Alive Directory", "url": "https://www.alivedirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Directory World", "url": "https://www.directoryworld.net", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "9sites", "url": "https://www.9sites.net", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Pegasus Directory", "url": "https://www.pegasusdirectory.com", "category": "Web Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Directory Journal", "url": "https://www.directoryjournal.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "One Mission", "url": "https://www.onemission.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "WEB Directory", "url": "https://www.webdirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Jasmine Directory", "url": "https://www.jasminedirectory.com", "category": "Web Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "1WebDirectory", "url": "https://www.1webdirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AllStatesUSA", "url": "https://www.allstatesusadirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Blogarama", "url": "https://www.blogarama.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Blog Starter", "url": "https://www.blogstarter.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Aviva Directory", "url": "https://www.avivadirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Directory Critic", "url": "https://www.directorycritic.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- INDIA - MORE DIRECTORIES ----
    {"name": "IndiaBusiness", "url": "https://www.indiabusiness.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaPages", "url": "https://www.indiapages.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaOnlineFlorists", "url": "https://www.indiaonlineflorists.com", "category": "Niche Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "CityInformatics", "url": "https://www.cityinformatics.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Bgyellowpages", "url": "https://www.bgyellowpages.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaBook", "url": "https://www.indiabook.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Jantareview", "url": "https://www.jantareview.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "MouthShut", "url": "https://www.mouthshut.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "WhoOwnsWhat", "url": "https://www.whoownswhat.in", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Freeadsinindia", "url": "https://www.freeadsinindia.in", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "DelhiDirectory", "url": "https://www.delhidirectory.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "MumbaiDirectory", "url": "https://www.mumbaidirectory.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "ChennaiDirectory", "url": "https://www.chennaidirectory.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BangaloreDirectory", "url": "https://www.bangaloredirectory.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Khojle", "url": "https://www.khojle.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "NiceLocal India", "url": "https://nicelocal.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Dealerbaba", "url": "https://www.dealerbaba.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BikaYi", "url": "https://www.bikayi.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Clocate India", "url": "https://www.clocate.com", "category": "Event Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Tradersnet India", "url": "https://www.tradersnet.in", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},

    # ---- MORE GLOBAL / NICHE DIRECTORIES ----
    {"name": "Yelp India", "url": "https://www.yelp.co.in", "category": "Review Site", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "Trustpilot", "url": "https://www.trustpilot.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Sitejabber", "url": "https://www.sitejabber.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ConsumerAffairs", "url": "https://www.consumeraffairs.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "PissedConsumer", "url": "https://www.pissedconsumer.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Moz Local", "url": "https://moz.com/products/local", "category": "Local Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "BrightLocal", "url": "https://www.brightlocal.com", "category": "Local Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "Yext", "url": "https://www.yext.com", "category": "Local Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "Factual", "url": "https://www.factual.com", "category": "Data Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Here.com", "url": "https://www.here.com", "category": "Map Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TomTom Places", "url": "https://www.tomtom.com", "category": "Map Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Navmii", "url": "https://www.navmii.com", "category": "Map Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "OpenStreetMap", "url": "https://www.openstreetmap.org", "category": "Map Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Waze Business", "url": "https://www.waze.com", "category": "Map Directory", "type": "Freemium", "link_type": "NoFollow", "country": "Global"},
    {"name": "iBegin", "url": "https://www.ibegin.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Insider Pages", "url": "https://www.insiderpages.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "CitySearch", "url": "https://www.citysearch.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "AmericanTowns", "url": "https://www.americantowns.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "BizSugar", "url": "https://www.bizsugar.com", "category": "Business Community", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "StartupNation", "url": "https://www.startupnation.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "F6S", "url": "https://www.f6s.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Gust", "url": "https://www.gust.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "KillerStartups", "url": "https://www.killerstartups.com", "category": "Startup Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "LaunchingNext", "url": "https://www.launchingnext.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "StartupBlink", "url": "https://www.startupblink.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "StartupRanking", "url": "https://www.startupranking.com", "category": "Startup Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TechDirectory", "url": "https://www.techdirectory.io", "category": "Tech Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "StackShare", "url": "https://stackshare.io", "category": "Tech Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Siftery", "url": "https://siftery.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "FinancesOnline", "url": "https://financesonline.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TrustRadius", "url": "https://www.trustradius.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PeerSpot", "url": "https://www.peerspot.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Crozdesk", "url": "https://crozdesk.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "CompareCamp", "url": "https://comparecamp.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Saasworthy", "url": "https://www.saasworthy.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DiscoverCloud", "url": "https://www.discovercloud.com", "category": "Software Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AllTopStartups", "url": "https://alltopstartups.com", "category": "Startup Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- MORE CLASSIFIEDS & FREE AD SITES ----
    {"name": "FreeAdLists", "url": "https://www.freeadlists.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Claz.org", "url": "https://www.claz.org", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "FreeAdsTime", "url": "https://www.freeadstime.org", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ClassifiedAds", "url": "https://www.classifiedads.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "FreeGlobalClassifiedAds", "url": "https://www.freeglobalclassifiedads.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "WallClassifieds", "url": "https://www.wallclassifieds.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AdsFree", "url": "https://www.adsfree.in", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "VivaStreet India", "url": "https://www.vivastreet.co.in", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "ClickIndia", "url": "https://www.clickindia.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Kugli", "url": "https://www.kugli.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Kedna", "url": "https://www.kedna.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Trovit", "url": "https://www.trovit.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Muamat", "url": "https://www.muamat.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PostAllFreeAds", "url": "https://www.postallfreeads.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AdsRiver", "url": "https://www.adsriver.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaListed", "url": "https://www.indialisted.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "FreeAd1", "url": "https://www.freead1.net", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "WallClassifieds India", "url": "https://in.wallclassifieds.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "GlobalAdvertisingForum", "url": "https://www.globaladvertisingforum.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SellBuyStuffs", "url": "https://www.sellbuystuffs.com", "category": "Classifieds", "type": "Free", "link_type": "DoFollow", "country": "India"},

    # ---- MORE WEB / ARTICLE DIRECTORIES ----
    {"name": "EZineArticles", "url": "https://www.ezinearticles.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ArticleBiz", "url": "https://www.articlebiz.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GoArticles", "url": "https://www.goarticles.info", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ArticlesXpert", "url": "https://www.articlesxpert.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SelfGrowth", "url": "https://www.selfgrowth.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "HubPages", "url": "https://www.hubpages.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Buzzle", "url": "https://www.buzzle.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ArticleBase", "url": "https://www.articlesbase.com", "category": "Article Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- BUSINESS PROFILE / LISTING AGGREGATORS ----
    {"name": "D&B (Dun & Bradstreet)", "url": "https://www.dnb.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "ZoomInfo", "url": "https://www.zoominfo.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Hoovers", "url": "https://www.hoovers.com", "category": "B2B Directory", "type": "Paid", "link_type": "DoFollow", "country": "US"},
    {"name": "Owler", "url": "https://www.owler.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Craft.co", "url": "https://craft.co", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "RocketReach", "url": "https://rocketreach.co", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Apollo.io", "url": "https://www.apollo.io", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "LeadIQ", "url": "https://leadiq.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "BuiltWith", "url": "https://builtwith.com", "category": "Tech Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "SimilarWeb", "url": "https://www.similarweb.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- NICHE / INDUSTRY DIRECTORIES ----
    {"name": "WeddingWire India", "url": "https://www.weddingwire.in", "category": "Wedding Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "WedMeGood", "url": "https://www.wedmegood.com", "category": "Wedding Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "ShaadiSaga", "url": "https://www.shaadisaga.com", "category": "Wedding Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "HappyWedding", "url": "https://www.happywedding.app", "category": "Wedding Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Zaubacorp", "url": "https://www.zaubacorp.com", "category": "Company Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Tofler", "url": "https://www.tofler.in", "category": "Company Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "India Filings", "url": "https://www.indiafilings.com", "category": "Business Services", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "ClearTax", "url": "https://www.cleartax.in", "category": "Business Services", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "JustEat India", "url": "https://www.just-eat.in", "category": "Food Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "DineOut", "url": "https://www.dineout.co.in", "category": "Food Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "EazyDiner", "url": "https://www.eazydiner.com", "category": "Food Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BookMyShow", "url": "https://www.bookmyshow.com", "category": "Entertainment Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Paytm Business", "url": "https://business.paytm.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Google Maps", "url": "https://maps.google.com", "category": "Map Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DesignRush", "url": "https://www.designrush.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Agency Spotter", "url": "https://www.agencyspotter.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Sortlist", "url": "https://www.sortlist.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "UpCity", "url": "https://upcity.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TopDevelopers", "url": "https://www.topdevelopers.co", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AppFutura", "url": "https://www.appfutura.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SelectedFirms", "url": "https://www.selectedfirms.co", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Extract.co", "url": "https://extract.co", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TopDesignFirms", "url": "https://topdesignfirms.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Manifest.co", "url": "https://themanifest.com", "category": "Agency Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- FREELANCE / SERVICE MARKETPLACES ----
    {"name": "Upwork", "url": "https://www.upwork.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Fiverr", "url": "https://www.fiverr.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Freelancer.com", "url": "https://www.freelancer.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Toptal", "url": "https://www.toptal.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PeoplePerHour", "url": "https://www.peopleperhour.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Guru.com", "url": "https://www.guru.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "99designs", "url": "https://99designs.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DesignCrowd", "url": "https://www.designcrowd.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Truelancer", "url": "https://www.truelancer.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "WorkNHire", "url": "https://www.worknhire.com", "category": "Freelance Marketplace", "type": "Free", "link_type": "DoFollow", "country": "India"},

    # ---- UK / EUROPE DIRECTORIES ----
    {"name": "Yell UK", "url": "https://www.yell.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "ThomsonLocal", "url": "https://www.thomsonlocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "FreeIndex", "url": "https://www.freeindex.co.uk", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "Scoot UK", "url": "https://www.scoot.co.uk", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "Central Index", "url": "https://www.centralindex.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "BrownBook UK", "url": "https://www.brownbook.net", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "Europages", "url": "https://www.europages.co.uk", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Europe"},
    {"name": "Qype", "url": "https://www.qype.co.uk", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "TouchLocal", "url": "https://www.touchlocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "Bark UK", "url": "https://www.bark.com", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "UK"},
    {"name": "MyBuilder", "url": "https://www.mybuilder.com", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "UK"},
    {"name": "Checkatrade", "url": "https://www.checkatrade.com", "category": "Service Directory", "type": "Paid", "link_type": "DoFollow", "country": "UK"},
    {"name": "TrustedTraders", "url": "https://www.trustedtraders.which.co.uk", "category": "Service Directory", "type": "Paid", "link_type": "DoFollow", "country": "UK"},
    {"name": "PagesDOr", "url": "https://www.pagesjaunes.fr", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "France"},
    {"name": "Gelbe Seiten", "url": "https://www.gelbeseiten.de", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Germany"},
    {"name": "PaginasAmarillas", "url": "https://www.paginasamarillas.es", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Spain"},

    # ---- AUSTRALIA / NZ ----
    {"name": "TrueLocal", "url": "https://www.truelocal.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "Yellow Pages AU", "url": "https://www.yellowpages.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "White Pages AU", "url": "https://www.whitepages.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "HotFrog AU", "url": "https://www.hotfrog.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "StartLocal AU", "url": "https://www.startlocal.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "DLook AU", "url": "https://www.dlook.com.au", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "NoCowboys NZ", "url": "https://www.nocowboys.co.nz", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "New Zealand"},
    {"name": "Yellow NZ", "url": "https://yellow.co.nz", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "New Zealand"},
    {"name": "Finda NZ", "url": "https://www.finda.co.nz", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "New Zealand"},

    # ---- CANADA ----
    {"name": "Yellow Pages CA", "url": "https://www.yellowpages.ca", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Canada"},
    {"name": "CanPages", "url": "https://www.canpages.ca", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Canada"},
    {"name": "411 Canada", "url": "https://www.411.ca", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Canada"},
    {"name": "ProfileCanada", "url": "https://www.profilecanada.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Canada"},
    {"name": "iBegin Canada", "url": "https://www.ibegin.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Canada"},

    # ---- MORE FREE DIRECTORY SITES ----
    {"name": "OneFlare", "url": "https://www.oneflare.com.au", "category": "Service Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "Bark Australia", "url": "https://www.bark.com/en/au", "category": "Service Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Australia"},
    {"name": "WhereToBuy", "url": "https://www.wheretobuy.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Find-Us-Here", "url": "https://www.find-us-here.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ListedIn", "url": "https://www.listedin.co.uk", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "Approved Index", "url": "https://www.approvedindex.co.uk", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "192.com Business", "url": "https://www.192.com", "category": "Local Directory", "type": "Freemium", "link_type": "DoFollow", "country": "UK"},
    {"name": "Bizify", "url": "https://www.bizify.co.uk", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "UK"},
    {"name": "YourLocalServices", "url": "https://www.yourlocalservices.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Infobel", "url": "https://www.infobel.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Cylex Global", "url": "https://www.cylex.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "MyLocalPage", "url": "https://www.mylocalpage.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "NearFindr", "url": "https://www.nearfindr.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Bizbooklocal", "url": "https://www.bizbooklocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ThreeBestRated", "url": "https://threebestrated.com", "category": "Review Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TopNLocal", "url": "https://www.topnlocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BookmarkBay", "url": "https://www.bookmarkbay.com", "category": "Bookmark Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ScoopIt", "url": "https://www.scoop.it", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Folkd", "url": "https://www.folkd.com", "category": "Bookmark Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Diigo", "url": "https://www.diigo.com", "category": "Bookmark Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Mix.com", "url": "https://mix.com", "category": "Bookmark Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BizCommunity", "url": "https://www.bizcommunity.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Spoke", "url": "https://www.spoke.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Cylex US", "url": "https://www.cylex.us.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "eBusinessPages", "url": "https://www.ebusinesspages.com", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Tupalo", "url": "https://www.tupalo.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GlobalCatalog", "url": "https://www.globalcatalog.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Go4WorldBusiness", "url": "https://www.go4worldbusiness.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "EC21", "url": "https://www.ec21.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ECPlaza", "url": "https://www.ecplaza.net", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TradeKey", "url": "https://www.tradekey.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Made-in-China", "url": "https://www.made-in-china.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GlobalSources", "url": "https://www.globalsources.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "DHGate", "url": "https://www.dhgate.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Alibaba", "url": "https://www.alibaba.com", "category": "B2B Directory", "type": "Freemium", "link_type": "NoFollow", "country": "Global"},
    {"name": "HKTDC", "url": "https://www.hktdc.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BizVibe", "url": "https://www.bizvibe.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "ExportHub", "url": "https://www.exporthub.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TradeFord", "url": "https://www.tradeford.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "eWorldTrade", "url": "https://www.eworldtrade.com", "category": "B2B Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "ConnectAmericas", "url": "https://connectamericas.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- ADDITIONAL INDIAN SITES ----
    {"name": "JustDial Lite", "url": "https://lite.justdial.com", "category": "Local Directory", "type": "Free", "link_type": "NoFollow", "country": "India"},
    {"name": "Dial4Trade", "url": "https://www.dial4trade.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Business List India", "url": "https://www.businesslist.co.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaBiz", "url": "https://www.indiabiz.in", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Vanik", "url": "https://www.vanik.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Pepagora", "url": "https://www.pepagora.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndianManufacturers", "url": "https://www.indianmanufacturers.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "HelloTradeOnline", "url": "https://www.hellotradeonline.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "IndiaTradeFair", "url": "https://www.indiatradefair.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "BuyerGuts India", "url": "https://www.buyerguts.com", "category": "B2B Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Tolet Global", "url": "https://www.tolet.com", "category": "Real Estate Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "Housing.com", "url": "https://www.housing.com", "category": "Real Estate Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "CommonFloor", "url": "https://www.commonfloor.com", "category": "Real Estate Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "NoBroker", "url": "https://www.nobroker.in", "category": "Real Estate Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},
    {"name": "Fastway India", "url": "https://www.fastway.in", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "StartupIndia", "url": "https://www.startupindia.gov.in", "category": "Government Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "MSME Databank", "url": "https://msmedatabank.in", "category": "Government Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "GeM Portal", "url": "https://gem.gov.in", "category": "Government Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "TenderDetail", "url": "https://www.tenderdetail.com", "category": "Government Directory", "type": "Freemium", "link_type": "DoFollow", "country": "India"},

    # ---- EDUCATION / TRAINING DIRECTORIES ----
    {"name": "CourseReport", "url": "https://www.coursereport.com", "category": "Education Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ClassCentral", "url": "https://www.classcentral.com", "category": "Education Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "CourseFinder", "url": "https://www.coursefinder.com.au", "category": "Education Directory", "type": "Free", "link_type": "DoFollow", "country": "Australia"},
    {"name": "Shiksha", "url": "https://www.shiksha.com", "category": "Education Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},
    {"name": "CollegeDekho", "url": "https://www.collegedekho.com", "category": "Education Directory", "type": "Free", "link_type": "DoFollow", "country": "India"},

    # ---- FORUM / COMMUNITY SITES ----
    {"name": "Warrior Forum", "url": "https://www.warriorforum.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DigitalPoint", "url": "https://www.digitalpoint.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BlackHatWorld", "url": "https://www.blackhatworld.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "WebmasterWorld", "url": "https://www.webmasterworld.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "VBulletin Forum", "url": "https://www.vbulletin.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SmallBusinessForum", "url": "https://www.smallbusinessbrief.com", "category": "Business Forum", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- MORE MISC DIRECTORIES ----
    {"name": "GoLocal", "url": "https://www.golocal247.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "DiscoverOurTown", "url": "https://www.discoverourtown.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "DirectoryBug", "url": "https://www.directorybug.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AddBusiness", "url": "https://www.addbusiness.net", "category": "Business Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "LinkCentre", "url": "https://www.linkcentre.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "FreeWebSubmission", "url": "https://www.freewebsubmission.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SubmitX", "url": "https://www.submitx.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AddURL", "url": "https://www.addurl.nu", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ExactSeek", "url": "https://www.exactseek.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SonicRun", "url": "https://www.sonicrun.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BigMouthMedia", "url": "https://www.bigmouthmedia.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "CannyLink", "url": "https://www.cannylink.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DirectMyLink", "url": "https://www.directmylink.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "FreeListings", "url": "https://www.freelistings.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "MassiveLinks", "url": "https://www.massivelinks.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "SearchSight", "url": "https://www.searchsight.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "TopOfBlogs", "url": "https://www.topofblogs.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BlogSearchEngine", "url": "https://www.blogsearchengine.org", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GlobeOfBlogs", "url": "https://www.globeofblogs.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BlogFlux", "url": "https://www.blogflux.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BlogCatalog", "url": "https://www.blogcatalog.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "OnTopList", "url": "https://www.ontoplist.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Blog Engage", "url": "https://www.blogengage.com", "category": "Blog Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "eLocal", "url": "https://www.elocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "FourSquare City", "url": "https://foursquare.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BirdEye Business", "url": "https://birdeye.com", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "Podium", "url": "https://www.podium.com", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "NiceJob", "url": "https://nicejob.com", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "Grade.us", "url": "https://grade.us", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "Reputation.com", "url": "https://www.reputation.com", "category": "Review Site", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "StatusBrew", "url": "https://statusbrew.com", "category": "Social Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Buffer", "url": "https://buffer.com", "category": "Social Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Mention", "url": "https://mention.com", "category": "Business Tool", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Brandwatch", "url": "https://www.brandwatch.com", "category": "Business Tool", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "MyCompanyWorks", "url": "https://www.mycompanyworks.com", "category": "Business Directory", "type": "Freemium", "link_type": "DoFollow", "country": "US"},

    # ---- PRESS RELEASE / NEWS SITES ----
    {"name": "PRLog", "url": "https://www.prlog.org", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PR.com", "url": "https://www.pr.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "OpenPR", "url": "https://www.openpr.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Free Press Release", "url": "https://www.free-press-release.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "1888PressRelease", "url": "https://www.1888pressrelease.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "NewswireToday", "url": "https://www.newswiretoday.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PRZoom", "url": "https://www.przoom.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "ClickPress", "url": "https://www.clickpress.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "PRBuzz", "url": "https://www.prbuzz.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "24-7PressRelease", "url": "https://www.24-7pressrelease.com", "category": "Press Release", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "PressReleasePoint", "url": "https://www.pressreleasepoint.com", "category": "Press Release", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "IssueWire", "url": "https://www.issuewire.com", "category": "Press Release", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- QUESTION/ANSWER & WIKI SITES ----
    {"name": "WikiAlpha", "url": "https://www.wikialpha.org", "category": "Wiki Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "EverybodyWiki", "url": "https://en.everybodywiki.com", "category": "Wiki Site", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Quora Spaces", "url": "https://www.quora.com", "category": "Q&A Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "StackExchange", "url": "https://stackexchange.com", "category": "Q&A Platform", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Answers.com", "url": "https://www.answers.com", "category": "Q&A Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- DOCUMENT / PDF SHARING ----
    {"name": "SlideServe", "url": "https://www.slideserve.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "AuthorStream", "url": "https://www.authorstream.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Edocr", "url": "https://www.edocr.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Scribd", "url": "https://www.scribd.com", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Calameo", "url": "https://www.calameo.com", "category": "Content Platform", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "FlipHTML5", "url": "https://fliphtml5.com", "category": "Content Platform", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- IMAGE / VIDEO SHARING ----
    {"name": "Flickr", "url": "https://www.flickr.com", "category": "Image Sharing", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "500px", "url": "https://500px.com", "category": "Image Sharing", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Imgur", "url": "https://imgur.com", "category": "Image Sharing", "type": "Free", "link_type": "NoFollow", "country": "Global"},
    {"name": "Vimeo", "url": "https://vimeo.com", "category": "Video Sharing", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Dailymotion", "url": "https://www.dailymotion.com", "category": "Video Sharing", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Metacafe", "url": "https://www.metacafe.com", "category": "Video Sharing", "type": "Free", "link_type": "DoFollow", "country": "Global"},

    # ---- PODCAST / AUDIO ----
    {"name": "Anchor.fm", "url": "https://anchor.fm", "category": "Podcast Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Podbean", "url": "https://www.podbean.com", "category": "Podcast Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "Buzzsprout", "url": "https://www.buzzsprout.com", "category": "Podcast Directory", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},
    {"name": "SoundCloud", "url": "https://soundcloud.com", "category": "Audio Sharing", "type": "Freemium", "link_type": "DoFollow", "country": "Global"},

    # ---- ADDITIONAL WEB DIRECTORIES ----
    {"name": "BOTW", "url": "https://botw.org", "category": "Web Directory", "type": "Paid", "link_type": "DoFollow", "country": "Global"},
    {"name": "ABLocal", "url": "https://www.ablocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "CityOf.com", "url": "https://www.cityof.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Cataloxy", "url": "https://www.cataloxy.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GlobeRunner", "url": "https://www.globerunner.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "USCity.net", "url": "https://www.uscity.net", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Where2go", "url": "https://www.where2go.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "BOTW Local", "url": "https://local.botw.org", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "ZipLocal", "url": "https://www.ziplocal.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "MyCity", "url": "https://www.mycity.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "Kudzu", "url": "https://www.kudzu.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "JustLanded", "url": "https://www.justlanded.com", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "CitySlick", "url": "https://www.cityslick.net", "category": "Local Directory", "type": "Free", "link_type": "DoFollow", "country": "US"},
    {"name": "DirectoryRanker", "url": "https://www.directoryranker.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DirectorySEO", "url": "https://www.directoryseo.biz", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DirectoryVault", "url": "https://www.directoryvault.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "GreatDirectories", "url": "https://www.greatdirectories.org", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Prolinkdirectory", "url": "https://www.prolinkdirectory.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "QualityDirList", "url": "https://www.qualitydirlist.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "DirectoryFire", "url": "https://www.directoryfire.com", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
    {"name": "Askmap", "url": "https://www.askmap.net", "category": "Web Directory", "type": "Free", "link_type": "DoFollow", "country": "Global"},
]


# ===========================================================
# SEARCH QUERIES — used to find articles listing directories
# ===========================================================

SEARCH_QUERIES = [
    "free business listing sites in India 2024",
    "top 500 business directory submission sites list",
    "free local business listing websites India",
    "high DA business listing sites",
    "dofollow business directory submission sites",
    "free classifieds sites India list",
    "best free business directories for SEO backlinks",
    "top Indian business listing websites free",
    "free online business directory submission sites list",
    "business listing sites with high domain authority",
    "free company listing websites India",
    "B2B listing sites India free",
    "free directory submission sites list 2024",
    "local SEO business listing sites India",
    "free web directory submission sites dofollow",
]


# ===========================================================
# WEB SCRAPING — find more listing sites from articles
# ===========================================================

def search_bing(query: str, count: int = 20) -> list:
    """Search Bing and return result URLs."""
    urls = []
    try:
        search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&count={count}"
        resp = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("li.b_algo h2 a"):
                href = a.get("href", "")
                if href.startswith("http"):
                    urls.append(href)
    except Exception as e:
        logger.debug(f"Bing search failed for '{query}': {e}")
    return urls


def search_google(query: str) -> list:
    """Search Google and return result URLs."""
    urls = []
    try:
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=15"
        google_headers = dict(HEADERS)
        google_headers["Accept"] = "text/html,application/xhtml+xml"
        resp = requests.get(search_url, headers=google_headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            # Extract URLs from Google's result page
            for match in re.findall(r'href="(/url\?q=|)(https?://[^"&]+)', resp.text):
                url = match[1]
                if "google.com" not in url and "googleapis.com" not in url:
                    urls.append(url)
    except Exception as e:
        logger.debug(f"Google search failed for '{query}': {e}")
    return urls


# Known blog articles that list business directories (reliable sources)
KNOWN_ARTICLE_URLS = [
    "https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview",
]


def extract_urls_from_article(article_url: str) -> list:
    """
    Scrape a blog article and extract all external URLs.
    These are potential business listing sites mentioned in the article.
    """
    found = []
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return found

        soup = BeautifulSoup(resp.text, "lxml")
        article_domain = urlparse(article_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href.startswith("http"):
                continue

            parsed = urlparse(href)
            domain = parsed.netloc.lower()

            # Skip same-domain, social shares, and common non-directory links
            skip_domains = {
                article_domain,
                "facebook.com", "twitter.com", "t.co", "linkedin.com",
                "pinterest.com", "instagram.com", "youtube.com",
                "google.com", "bing.com", "yahoo.com",
                "amazon.com", "flipkart.com", "snapdeal.com",
                "bit.ly", "goo.gl", "tinyurl.com",
                "w3.org", "schema.org", "wordpress.org",
            }

            if any(skip in domain for skip in skip_domains):
                continue

            # Normalize URL to homepage
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            link_text = a.get_text(strip=True)
            name = link_text if link_text and len(link_text) < 80 else domain.replace("www.", "")

            found.append({
                "name": name,
                "url": base_url,
                "category": "Directory",
                "type": "Unknown",
                "link_type": "Unknown",
                "country": "Unknown",
            })

    except Exception as e:
        logger.debug(f"Failed to scrape article {article_url}: {e}")

    return found


def scrape_web_for_sites() -> list:
    """
    Search the web for articles listing business directories,
    then extract URLs from those articles.
    """
    logger.info("Searching the web for business listing site articles...")
    all_found = []
    article_urls = set()

    # Step 0: Add known articles
    for url in KNOWN_ARTICLE_URLS:
        article_urls.add(url)

    # Step 1: Find articles via search engines
    for i, query in enumerate(SEARCH_QUERIES):
        logger.info(f"  Searching ({i+1}/{len(SEARCH_QUERIES)}): {query[:50]}...")
        # Try Bing
        results = search_bing(query)
        for url in results:
            article_urls.add(url)
        # Try Google too
        results = search_google(query)
        for url in results:
            article_urls.add(url)
        time.sleep(1.5)  # Be polite

    logger.info(f"Found {len(article_urls)} articles to scrape")

    # Step 2: Scrape each article for listing site URLs
    for i, article_url in enumerate(article_urls):
        logger.info(f"Scraping article {i+1}/{len(article_urls)}: {article_url[:80]}...")
        sites = extract_urls_from_article(article_url)
        all_found.extend(sites)
        time.sleep(0.5)

    logger.info(f"Extracted {len(all_found)} raw URLs from articles")
    return all_found


# ===========================================================
# URL VALIDATION — check if sites are live
# ===========================================================

def validate_url(site: dict) -> dict:
    """Check if a URL is reachable and add status."""
    url = site["url"]
    try:
        resp = requests.head(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code < 400:
            site["status"] = "Live"
            # Update URL if redirected
            if resp.url and resp.url != url:
                site["url"] = f"{urlparse(resp.url).scheme}://{urlparse(resp.url).netloc}"
        else:
            site["status"] = f"Error ({resp.status_code})"
    except requests.exceptions.SSLError:
        # Try without HTTPS
        try:
            fallback = url.replace("https://", "http://")
            resp = requests.head(fallback, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            site["status"] = "Live (HTTP only)"
            site["url"] = fallback
        except Exception:
            site["status"] = "Dead"
    except Exception:
        site["status"] = "Dead"

    return site


def validate_sites(sites: list) -> list:
    """Validate all site URLs concurrently."""
    logger.info(f"Validating {len(sites)} URLs (this may take a few minutes)...")
    validated = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(validate_url, site): site for site in sites}
        done = 0
        for future in as_completed(futures):
            done += 1
            if done % 50 == 0:
                logger.info(f"  Validated {done}/{len(sites)}...")
            try:
                result = future.result()
                validated.append(result)
            except Exception:
                site = futures[future]
                site["status"] = "Error"
                validated.append(site)

    live = sum(1 for s in validated if "Live" in s.get("status", ""))
    logger.info(f"Validation complete: {live} live, {len(validated) - live} dead/error")
    return validated


# ===========================================================
# DOMAIN AUTHORITY — via OpenPageRank free API
# ===========================================================

def fetch_da_batch(domains: list) -> dict:
    """
    Fetch Domain Authority for a batch of domains using OpenPageRank API.
    Free tier: 10,000 requests/day (up to 100 domains per request).
    Sign up at: https://www.domcop.com/openpagerank/auth/signup
    """
    if not OPENPAGERANK_API_KEY:
        return {}

    da_map = {}
    # API accepts up to 100 domains per request
    batch_size = 100

    for i in range(0, len(domains), batch_size):
        batch = domains[i:i + batch_size]
        try:
            params = [("domains[]", d) for d in batch]
            resp = requests.get(
                "https://openpagerank.com/api/v1.0/getPageRank",
                params=params,
                headers={"API-OPR": OPENPAGERANK_API_KEY},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("response", []):
                    domain = item.get("domain", "")
                    da = item.get("page_rank_decimal", 0)
                    if domain and da:
                        da_map[domain] = round(da, 1)
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"DA fetch failed for batch: {e}")

    return da_map


def enrich_with_da(sites: list) -> list:
    """Add Domain Authority to each site record."""
    if not OPENPAGERANK_API_KEY:
        logger.info("DA check skipped (no OpenPageRank API key set)")
        logger.info("Get a free key at: https://www.domcop.com/openpagerank/auth/signup")
        for site in sites:
            site["da"] = ""
        return sites

    logger.info("Fetching Domain Authority scores...")
    domains = []
    for site in sites:
        parsed = urlparse(site["url"])
        domain = parsed.netloc.replace("www.", "")
        domains.append(domain)

    da_map = fetch_da_batch(domains)

    for site in sites:
        parsed = urlparse(site["url"])
        domain = parsed.netloc.replace("www.", "")
        site["da"] = da_map.get(domain, "")

    found_da = sum(1 for s in sites if s.get("da"))
    logger.info(f"DA scores found for {found_da}/{len(sites)} sites")
    return sites


# ===========================================================
# DEDUPLICATION & CLEANUP
# ===========================================================

def deduplicate_sites(sites: list) -> list:
    """Remove duplicate sites based on domain name."""
    seen = set()
    unique = []

    for site in sites:
        parsed = urlparse(site["url"])
        domain = parsed.netloc.lower().replace("www.", "")

        if domain and domain not in seen:
            seen.add(domain)
            # Clean up the name
            name = site.get("name", "").strip()
            if not name or len(name) < 2:
                name = domain
            site["name"] = name
            unique.append(site)

    logger.info(f"Deduplication: {len(sites)} -> {len(unique)} unique sites")
    return unique


# ===========================================================
# EXPORT
# ===========================================================

EXPORT_COLUMNS = [
    "name", "url", "da", "type", "link_type",
    "category", "country", "status",
]

EXPORT_HEADERS = [
    "Website Name", "URL", "Domain Authority", "Type (Free/Paid)",
    "Link Type (DoFollow/NoFollow)", "Category", "Country", "Status",
]


def export_csv(sites: list, filepath: str):
    """Export sites to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(sites)

    # Ensure all columns exist
    for col in EXPORT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[EXPORT_COLUMNS]
    df.columns = EXPORT_HEADERS
    df.to_csv(filepath, index=False)
    logger.info(f"CSV saved: {filepath} ({len(df)} sites)")


def export_excel(sites: list, filepath: str):
    """Export sites to Excel with formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(sites)

    for col in EXPORT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[EXPORT_COLUMNS]
    df.columns = EXPORT_HEADERS
    df.to_excel(filepath, index=False)
    logger.info(f"Excel saved: {filepath} ({len(df)} sites)")


def open_file(filepath: str):
    """Open file with OS default application."""
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        return
    logger.info(f"Opening: {filepath}")
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        logger.warning(f"Could not auto-open: {e}")


# ===========================================================
# MAIN PIPELINE
# ===========================================================

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Find 1000+ business listing sites for directory submission & backlinks",
    )
    parser.add_argument("--skip-validate", action="store_true", help="Skip URL live-check (faster)")
    parser.add_argument("--excel", action="store_true", help="Also export to Excel (.xlsx)")
    parser.add_argument("--da", action="store_true", help="Fetch Domain Authority (needs API key)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the output file")
    parser.add_argument("--seed-only", action="store_true", help="Use only seed data, skip web scraping")
    args = parser.parse_args()

    logger.info("")
    logger.info("=" * 55)
    logger.info("  BUSINESS LISTING SITE FINDER")
    logger.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 55)

    # ---- Step 1: Start with seed database ----
    all_sites = list(SEED_SITES)
    logger.info(f"Seed database: {len(all_sites)} known sites")

    # ---- Step 2: Scrape web for more sites ----
    if not args.seed_only:
        web_sites = scrape_web_for_sites()
        all_sites.extend(web_sites)
        logger.info(f"Total before dedup: {len(all_sites)}")

    # ---- Step 3: Deduplicate ----
    all_sites = deduplicate_sites(all_sites)

    # ---- Step 4: Validate URLs (optional) ----
    if not args.skip_validate:
        all_sites = validate_sites(all_sites)
    else:
        for site in all_sites:
            site["status"] = "Not checked"
        logger.info("Skipping URL validation (--skip-validate)")

    # ---- Step 5: Domain Authority (optional) ----
    if args.da:
        all_sites = enrich_with_da(all_sites)
    else:
        for site in all_sites:
            site.setdefault("da", "")

    # ---- Step 6: Sort by DA (if available), then by name ----
    def sort_key(s):
        da = s.get("da", "") or 0
        try:
            da = float(da)
        except (ValueError, TypeError):
            da = 0
        return (-da, s.get("name", "").lower())

    all_sites.sort(key=sort_key)

    # ---- Step 7: Export ----
    export_csv(all_sites, OUTPUT_CSV)

    if args.excel:
        export_excel(all_sites, OUTPUT_XLSX)

    # ---- Step 8: Auto-open ----
    if not args.no_open:
        output_path = OUTPUT_XLSX if args.excel else OUTPUT_CSV
        open_file(output_path)

    # ---- Summary ----
    logger.info("")
    logger.info("=" * 55)
    logger.info(f"  DONE! {len(all_sites)} business listing sites collected")
    logger.info(f"  CSV: {OUTPUT_CSV}")
    if args.excel:
        logger.info(f"  Excel: {OUTPUT_XLSX}")
    logger.info("=" * 55)
    logger.info("")


if __name__ == "__main__":
    main()
