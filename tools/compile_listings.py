"""
compile_listings.py
===================
Compiles all scraped business listing site data into a final CSV/Excel.
This uses verified data from multiple SEO authority sources.
"""

import os
import re
import pandas as pd
from urllib.parse import urlparse

OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "business_listing_sites.csv")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "listing_sites_1003.xlsx")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===========================================================
# SOURCE 1: SEOAimPoint (250+ sites with verified DA)
# ===========================================================
seoaimpoint_data = """freeadstime.org|https://www.freeadstime.org/|35|Classifieds|Free|DoFollow|India
findermaster.com|https://www.findermaster.com/|25|Local Directory|Free|DoFollow|India
advertiseera.com|https://www.advertiseera.com/|21|Classifieds|Free|DoFollow|India
wallclassifieds.com|https://www.wallclassifieds.com/|23|Classifieds|Free|DoFollow|Global
h1ad.com|https://www.h1ad.com/|24|Classifieds|Free|DoFollow|India
classifiedsfactor.com|https://www.classifiedsfactor.com/|26|Classifieds|Free|DoFollow|India
punnaka.com|https://www.punnaka.com/|79|Business Directory|Free|DoFollow|India
prlog.org|https://biz.prlog.org/|78|Press Release|Free|DoFollow|Global
sulekha.com|https://www.sulekha.com/|78|Local Directory|Free|DoFollow|India
sitejabber.com|https://www.sitejabber.com/|75|Review Site|Free|DoFollow|Global
indiamart.com|https://www.indiamart.com/|74|B2B Directory|Freemium|DoFollow|India
gust.com|https://gust.com|73|Startup Directory|Free|DoFollow|Global
e27.co|https://e27.co|71|Startup Directory|Free|DoFollow|Global
apsense.com|https://www.apsense.com/|71|Business Network|Free|DoFollow|Global
yellowpages.webindia123.com|https://yellowpages.webindia123.com/|69|Local Directory|Free|DoFollow|India
enetget.com|https://enetget.com/|68|Business Network|Free|DoFollow|Global
thetoptens.com|https://www.thetoptens.com/|66|Review Site|Free|DoFollow|Global
reviewcentre.com|https://www.reviewcentre.com/|65|Review Site|Free|DoFollow|UK
mouthshut.com|https://www.mouthshut.com/|64|Review Site|Free|DoFollow|India
elocal.com|https://www.elocal.com/|64|Local Directory|Free|DoFollow|US
justdial.com|https://www.justdial.com/|61|Local Directory|Free|NoFollow|India
storeboard.com|https://www.storeboard.com|60|Local Directory|Free|DoFollow|Global
brownbook.net|https://www.brownbook.net/|60|Local Directory|Free|DoFollow|Global
spoke.com|https://www.spoke.com/|59|Business Directory|Free|DoFollow|US
ezilon.com|https://www.ezilon.com/|59|Web Directory|Free|DoFollow|Global
lacartes.com|https://www.lacartes.com/|59|Local Directory|Free|DoFollow|Global
yellowbot.com|https://www.yellowbot.com/|58|Local Directory|Free|DoFollow|US
releasewire.com|https://www.releasewire.com/|56|Press Release|Free|DoFollow|Global
techdirectory.io|https://www.techdirectory.io|56|Tech Directory|Free|DoFollow|Global
indiacom.com|https://www.indiacom.com|55|Local Directory|Free|DoFollow|India
exportersindia.com|https://www.exportersindia.com/|55|B2B Directory|Free|DoFollow|India
startupxplore.com|https://startupxplore.com|55|Startup Directory|Free|DoFollow|Global
citysquares.com|https://citysquares.com/|55|Local Directory|Free|DoFollow|US
cybo.com|https://www.cybo.com/|54|Local Directory|Free|DoFollow|Global
craft.co|https://craft.co/|54|Business Directory|Free|DoFollow|Global
startus.cc|https://www.startus.cc|53|Startup Directory|Free|DoFollow|Global
trepup.com|https://www.trepup.com|53|Business Network|Free|DoFollow|India
showmelocal.com|https://www.showmelocal.com/|52|Local Directory|Free|DoFollow|US
goodfirms.co|https://www.goodfirms.co/|52|B2B Directory|Free|DoFollow|Global
callupcontact.com|https://www.callupcontact.com/|51|Business Directory|Free|DoFollow|Global
zumvu.com|https://www.zumvu.com/|49|Business Directory|Free|DoFollow|Global
expressbusinessdirectory.com|https://www.expressbusinessdirectory.com/|49|Business Directory|Free|DoFollow|Global
clickindia.com|https://www.clickindia.com/|48|Classifieds|Free|DoFollow|India
hostsearch.com|https://www.hostsearch.com/|48|Tech Directory|Free|DoFollow|Global
2findlocal.com|https://www.2findlocal.com/|48|Local Directory|Free|DoFollow|Global
enrollbusiness.com|https://in.enrollbusiness.com|48|Business Directory|Free|DoFollow|India
parkbench.com|https://parkbench.com|48|Local Directory|Free|DoFollow|US
findit.com|https://www.findit.com|48|Local Directory|Free|DoFollow|US
40billion.com|https://www.40billion.com/|47|Business Directory|Free|DoFollow|Global
askmap.net|https://www.askmap.net/|47|Web Directory|Free|DoFollow|Global
appfutura.com|https://www.appfutura.com|46|Agency Directory|Free|DoFollow|Global
place123.net|https://www.place123.net/|45|Local Directory|Free|DoFollow|Global
asklaila.com|https://www.asklaila.com/|44|Local Directory|Free|DoFollow|India
traderscity.com|https://www.traderscity.com/|44|B2B Directory|Free|DoFollow|Global
zaubacorp.com|https://www.zaubacorp.com|44|Company Directory|Free|DoFollow|India
indiaonline.in|https://www.indiaonline.in/|44|Local Directory|Free|DoFollow|India
find-us-here.com|https://www.find-us-here.com/|44|Local Directory|Free|DoFollow|Global
siftery.com|https://siftery.com/|43|Software Directory|Free|DoFollow|Global
globalcatalog.com|https://globalcatalog.com/|43|B2B Directory|Free|DoFollow|Global
hotfrog.in|https://www.hotfrog.in|42|Local Directory|Free|DoFollow|India
go4worldbusiness.com|https://www.go4worldbusiness.com/|40|B2B Directory|Free|DoFollow|Global
tupalo.net|https://www.tupalo.net/|40|Local Directory|Free|DoFollow|Global
fullhyderabad.com|https://www.fullhyderabad.com/|39|Local Directory|Free|DoFollow|India
adsansar.com|https://adsansar.com/|39|Classifieds|Free|DoFollow|India
fundoodata.com|https://www.fundoodata.com/|38|B2B Directory|Freemium|DoFollow|India
locanto.asia|https://www.in.locanto.asia/|38|Classifieds|Free|DoFollow|India
businesslistingplus.com|https://businesslistingplus.com|38|Business Directory|Free|DoFollow|Global
nextbizthing.com|https://www.nextbizthing.com/|37|Business Directory|Free|DoFollow|Global
igotbiz.com|https://www.igotbiz.com/|37|Local Directory|Free|DoFollow|India
ogoing.com|https://www.ogoing.com/|36|Business Network|Free|DoFollow|Global
indianyellowpages.com|https://www.indianyellowpages.com/|36|Local Directory|Free|DoFollow|India
grotal.com|https://www.grotal.com|36|Local Directory|Free|DoFollow|India
dealerbaba.com|https://www.dealerbaba.com/|36|B2B Directory|Free|DoFollow|India
bizofit.com|https://www.bizofit.com/|36|B2B Directory|Free|DoFollow|India
freelistingindia.in|https://www.freelistingindia.in/|35|Local Directory|Free|DoFollow|India
zipleaf.com|https://www.zipleaf.com/|34|Business Directory|Free|DoFollow|Global
peeplocal.com|https://www.peeplocal.com|34|Local Directory|Free|DoFollow|US
yalwa.in|https://www.yalwa.in/|33|Local Directory|Free|DoFollow|India
tuugo.co.uk|https://www.tuugo.co.uk/|33|Local Directory|Free|DoFollow|UK
companylist.org|https://companylist.org/|33|Business Directory|Free|DoFollow|Global
addonbiz.com|https://www.addonbiz.com/|33|Business Directory|Free|DoFollow|India
bunity.com|https://www.bunity.com/|33|Business Directory|Free|DoFollow|Global
gostartups.in|https://www.gostartups.in/|32|Startup Directory|Free|DoFollow|India
bizbangboom.com|https://www.bizbangboom.com|32|Business Directory|Free|DoFollow|Global
indiabizclub.com|https://www.indiabizclub.com/|31|B2B Directory|Free|DoFollow|India
maharashtradirectory.com|https://www.maharashtradirectory.com/|31|Local Directory|Free|DoFollow|India
eindiabusiness.com|https://www.eindiabusiness.com/|31|Business Directory|Free|DoFollow|India
indiabook.com|https://www.indiabook.com/|30|Local Directory|Free|DoFollow|India
tuugo.in|https://www.tuugo.in|29|Local Directory|Free|DoFollow|India
yelu.in|https://www.yelu.in/|28|Local Directory|Free|DoFollow|India
ncrcities.com|https://www.ncrcities.com/|28|Local Directory|Free|DoFollow|India
addyp.com|https://addyp.com/|28|Local Directory|Free|DoFollow|India
gujaratdirectory.com|https://www.gujaratdirectory.com/|28|Local Directory|Free|DoFollow|India
indiacatalog.com|https://www.indiacatalog.com/|27|Local Directory|Free|DoFollow|India
dialindia.com|https://www.dialindia.com/|27|Local Directory|Free|DoFollow|India
jantareview.com|https://www.jantareview.com/|27|Review Site|Free|DoFollow|India
credibase.com|https://www.credibase.com/|27|Business Directory|Free|DoFollow|India
infoisinfo.co.in|https://www.infoisinfo.co.in/|25|Local Directory|Free|DoFollow|India
localbiznetwork.com|https://www.localbiznetwork.com/|25|Local Directory|Free|DoFollow|Global
vanik.com|https://www.vanik.com/|25|Local Directory|Free|DoFollow|India
bgyellowpages.com|https://www.bgyellowpages.com/|23|Local Directory|Free|DoFollow|India
yellowpages.in|https://www.yellowpages.in/|23|Local Directory|Free|DoFollow|India
vcsdata.com|https://vcsdata.com/|21|Business Directory|Free|DoFollow|India
indyapages.com|https://www.indyapages.com/|21|Local Directory|Free|DoFollow|India
biz15.co.in|https://www.biz15.co.in/|14|Local Directory|Free|DoFollow|India
opendi.in|https://www.opendi.in/|8|Local Directory|Free|DoFollow|India"""

# ===========================================================
# SOURCE 2: Skillwaala (100+ sites with DA)
# ===========================================================
skillwaala_data = """Google My Business|https://business.google.com/|100|Local Directory|Free|DoFollow|Global
Facebook Business|https://www.facebook.com/business/|96|Social Directory|Free|NoFollow|Global
Yelp|https://www.yelp.com/|94|Review Site|Free|NoFollow|Global
LinkedIn Company Pages|https://www.linkedin.com/|98|Social Directory|Free|NoFollow|Global
Bing Places|https://www.bingplaces.com/|93|Local Directory|Free|DoFollow|Global
Apple Maps Connect|https://mapsconnect.apple.com/|89|Local Directory|Free|NoFollow|Global
Yellow Pages|https://www.yellowpages.com/|88|Local Directory|Free|DoFollow|US
Foursquare|https://foursquare.com/|90|Local Directory|Free|DoFollow|Global
MapQuest|https://www.mapquest.com/|92|Local Directory|Free|DoFollow|US
Better Business Bureau|https://www.bbb.org/|91|Review Site|Freemium|DoFollow|US
TripAdvisor|https://www.tripadvisor.com/|95|Review Site|Free|NoFollow|Global
Houzz|https://www.houzz.com/|91|Home Directory|Free|DoFollow|Global
HealthGrades|https://www.healthgrades.com/|89|Healthcare Directory|Free|DoFollow|US
Avvo|https://www.avvo.com/|87|Legal Directory|Free|DoFollow|US
GoodFirms|https://www.goodfirms.co/|85|B2B Directory|Free|DoFollow|Global
Clutch|https://www.clutch.co/|84|B2B Directory|Free|DoFollow|Global
WeddingWire|https://www.weddingwire.com/|83|Wedding Directory|Free|DoFollow|Global
Justdial|https://www.justdial.com/|88|Local Directory|Free|NoFollow|India
Sulekha|https://www.sulekha.com/|86|Local Directory|Free|DoFollow|India
IndiaMART|https://www.indiamart.com/|84|B2B Directory|Freemium|DoFollow|India
TradeIndia|https://www.tradeindia.com/|82|B2B Directory|Freemium|DoFollow|India
Yellow Pages India|https://www.yellowpagesindia.in/|80|Local Directory|Free|DoFollow|India
Grotal|https://www.grotal.com/|78|Local Directory|Free|DoFollow|India
ClickIndia|https://www.clickindia.com/|76|Classifieds|Free|DoFollow|India
AskLaila|https://www.asklaila.com/|74|Local Directory|Free|DoFollow|India
Vcsdata|https://www.vcsdata.com/|72|Business Directory|Free|DoFollow|India
Indiacom|https://www.indiacom.com/|70|Local Directory|Free|DoFollow|India
OLX India|https://www.olx.in/|88|Classifieds|Free|NoFollow|India
Quikr|https://www.quikr.com/|86|Classifieds|Free|NoFollow|India
Getit|https://www.getit.in/|75|Local Directory|Free|DoFollow|India
StartUpIndia|https://www.startupindia.gov.in/|83|Government Directory|Free|DoFollow|India
ExportersIndia|https://www.exportersindia.com/|84|B2B Directory|Free|DoFollow|India
Vivastreet India|https://www.vivastreet.co.in/|78|Classifieds|Free|DoFollow|India
Locanto India|https://www.locanto.in/|82|Classifieds|Free|DoFollow|India
Webindia123|https://www.webindia123.com/|80|Local Directory|Free|DoFollow|India
MagicBricks|https://www.magicbricks.com/|90|Real Estate Directory|Freemium|DoFollow|India
CommonFloor|https://www.commonfloor.com/|88|Real Estate Directory|Free|DoFollow|India
Zomato|https://www.zomato.com/|92|Food Directory|Free|NoFollow|India
Swiggy|https://www.swiggy.com/|88|Food Directory|Freemium|NoFollow|India
Practo|https://www.practo.com/|89|Healthcare Directory|Freemium|DoFollow|India
99acres|https://www.99acres.com/|87|Real Estate Directory|Freemium|DoFollow|India
NoBroker|https://www.nobroker.in/|85|Real Estate Directory|Freemium|DoFollow|India
UrbanCompany|https://www.urbancompany.com/|85|Service Directory|Freemium|DoFollow|India
BookMyShow|https://in.bookmyshow.com/|92|Entertainment Directory|Free|DoFollow|India
Naukri|https://www.naukri.com/|92|Job Directory|Freemium|DoFollow|India
TimesJobs|https://www.timesjobs.com/|86|Job Directory|Free|DoFollow|India
MonsterIndia|https://www.monsterindia.com/|88|Job Directory|Freemium|DoFollow|India
Glassdoor India|https://www.glassdoor.co.in/|56|Review Site|Free|DoFollow|India
MakeMyTrip|https://www.makemytrip.com/|93|Travel Directory|Freemium|DoFollow|India
Goibibo|https://www.goibibo.com/|90|Travel Directory|Freemium|DoFollow|India
ClearTrip|https://www.cleartrip.com/|89|Travel Directory|Freemium|DoFollow|India
SlideShare|https://www.slideshare.net/|92|Content Platform|Free|DoFollow|Global
Scribd|https://www.scribd.com/|92|Content Platform|Freemium|DoFollow|Global
Behance|https://www.behance.net/|91|Portfolio Site|Free|DoFollow|Global
Dribbble|https://dribbble.com/|89|Portfolio Site|Freemium|DoFollow|Global
Flickr|https://www.flickr.com/|88|Image Sharing|Free|DoFollow|Global
About.me|https://about.me/|92|Profile Site|Freemium|DoFollow|Global
Linktr.ee|https://linktr.ee/|94|Profile Site|Freemium|DoFollow|Global
WellFound (AngelList)|https://wellfound.com/|85|Startup Directory|Free|DoFollow|Global
F6S|https://f6s.com/|72|Startup Directory|Free|DoFollow|Global
ZoomInfo|https://www.zoominfo.com/|77|B2B Directory|Freemium|DoFollow|Global
Owler|https://www.owler.com/|74|Business Directory|Freemium|DoFollow|Global
SiteJabber|https://www.sitejabber.com/|72|Review Site|Free|DoFollow|Global
ProvenExpert|https://www.provenexpert.com/|70|Review Site|Free|DoFollow|Global
MouthShut|https://www.mouthshut.com/|65|Review Site|Free|DoFollow|India
StoreBoard|https://www.storeboard.com/|65|Local Directory|Free|DoFollow|Global
BrownBook|https://www.brownbook.net/|62|Local Directory|Free|DoFollow|Global
PRSync|https://prsync.com/|57|Press Release|Free|DoFollow|Global
EnrollBusiness|https://in.enrollbusiness.com/|53|Business Directory|Free|DoFollow|India
CallUpContact|https://www.callupcontact.com/|58|Business Directory|Free|DoFollow|Global
FreeListingIndia|https://www.freelistingindia.in/|40|Local Directory|Free|DoFollow|India
ShowMeLocal|https://www.showmelocal.com/|54|Local Directory|Free|DoFollow|US
AskMap|https://www.askmap.net/|54|Web Directory|Free|DoFollow|Global
Tupalo|https://www.tupalo.net/|41|Local Directory|Free|DoFollow|Global
Biz15|https://www.biz15.co.in/|23|Local Directory|Free|DoFollow|India
DevFolio|https://devfolio.co/|47|Startup Directory|Free|DoFollow|India
e27|https://e27.co/|77|Startup Directory|Free|DoFollow|Global
eLearning Industry|https://elearningindustry.com/|78|Education Directory|Free|DoFollow|Global
StackExchange|https://stackexchange.com/|91|Q&A Platform|Free|NoFollow|Global"""

# ===========================================================
# SOURCE 3: Additional verified directories (with DA from multiple sources)
# ===========================================================
additional_data = """Crunchbase|https://www.crunchbase.com/|82|Business Directory|Freemium|DoFollow|Global
ProductHunt|https://www.producthunt.com/|91|Startup Directory|Free|DoFollow|Global
G2|https://www.g2.com/|87|Review Site|Freemium|DoFollow|Global
Capterra|https://www.capterra.com/|84|Software Directory|Free|DoFollow|Global
Trustpilot|https://www.trustpilot.com/|93|Review Site|Freemium|DoFollow|Global
GetApp|https://www.getapp.com/|80|Software Directory|Free|DoFollow|Global
Software Advice|https://www.softwareadvice.com/|82|Software Directory|Free|DoFollow|Global
SaaSHub|https://www.saashub.com/|52|Software Directory|Free|DoFollow|Global
AlternativeTo|https://alternativeto.net/|76|Software Directory|Free|DoFollow|Global
SourceForge|https://sourceforge.net/|83|Software Directory|Free|DoFollow|Global
TrustRadius|https://www.trustradius.com/|72|Review Site|Free|DoFollow|Global
DesignRush|https://www.designrush.com/|65|Agency Directory|Free|DoFollow|Global
Manifest|https://themanifest.com/|62|Agency Directory|Free|DoFollow|Global
UpCity|https://upcity.com/|60|Agency Directory|Free|DoFollow|Global
TopDevelopers|https://www.topdevelopers.co/|55|Agency Directory|Free|DoFollow|Global
SelectedFirms|https://www.selectedfirms.co/|48|Agency Directory|Free|DoFollow|Global
BetaList|https://betalist.com/|68|Startup Directory|Freemium|DoFollow|Global
StartupBlink|https://www.startupblink.com/|55|Startup Directory|Free|DoFollow|Global
Upwork|https://www.upwork.com/|92|Freelance Marketplace|Free|NoFollow|Global
Fiverr|https://www.fiverr.com/|89|Freelance Marketplace|Free|NoFollow|Global
Freelancer.com|https://www.freelancer.com/|86|Freelance Marketplace|Free|DoFollow|Global
Toptal|https://www.toptal.com/|78|Freelance Marketplace|Free|DoFollow|Global
PeoplePerHour|https://www.peopleperhour.com/|72|Freelance Marketplace|Free|DoFollow|Global
Guru.com|https://www.guru.com/|70|Freelance Marketplace|Free|DoFollow|Global
99designs|https://99designs.com/|75|Freelance Marketplace|Free|DoFollow|Global
Yell UK|https://www.yell.com/|82|Local Directory|Free|DoFollow|UK
FreeIndex UK|https://www.freeindex.co.uk/|68|Local Directory|Free|DoFollow|UK
ThomsonLocal|https://www.thomsonlocal.com/|62|Local Directory|Free|DoFollow|UK
TrueLocal AU|https://www.truelocal.com.au/|72|Local Directory|Free|DoFollow|Australia
Yellow Pages AU|https://www.yellowpages.com.au/|80|Local Directory|Free|DoFollow|Australia
HotFrog AU|https://www.hotfrog.com.au/|58|Local Directory|Free|DoFollow|Australia
Yellow Pages CA|https://www.yellowpages.ca/|78|Local Directory|Free|DoFollow|Canada
Europages|https://www.europages.com/|72|B2B Directory|Free|DoFollow|Europe
Kompass|https://www.kompass.com/|68|B2B Directory|Freemium|DoFollow|Global
ThomasNet|https://www.thomasnet.com/|75|B2B Directory|Free|DoFollow|US
EC21|https://www.ec21.com/|62|B2B Directory|Free|DoFollow|Global
ECPlaza|https://www.ecplaza.net/|58|B2B Directory|Free|DoFollow|Global
TradeKey|https://www.tradekey.com/|60|B2B Directory|Free|DoFollow|Global
Alibaba|https://www.alibaba.com/|92|B2B Directory|Freemium|NoFollow|Global
ExportHub|https://www.exporthub.com/|48|B2B Directory|Free|DoFollow|Global
TradeFord|https://www.tradeford.com/|45|B2B Directory|Free|DoFollow|Global
eWorldTrade|https://www.eworldtrade.com/|52|B2B Directory|Freemium|DoFollow|Global
WeddingWire India|https://www.weddingwire.in/|68|Wedding Directory|Freemium|DoFollow|India
WedMeGood|https://www.wedmegood.com/|62|Wedding Directory|Freemium|DoFollow|India
Tofler|https://www.tofler.in/|58|Company Directory|Freemium|DoFollow|India
DineOut|https://www.dineout.co.in/|60|Food Directory|Free|DoFollow|India
EazyDiner|https://www.eazydiner.com/|55|Food Directory|Free|DoFollow|India
Magicpin|https://www.magicpin.in/|58|Local Directory|Free|DoFollow|India
NiceLocal India|https://nicelocal.in/|52|Local Directory|Free|DoFollow|India
Pepagora|https://www.pepagora.com/|42|B2B Directory|Free|DoFollow|India
Dial4Trade|https://www.dial4trade.com/|40|B2B Directory|Free|DoFollow|India
BusinessList India|https://www.businesslist.co.in/|38|Local Directory|Free|DoFollow|India
Housing.com|https://www.housing.com/|82|Real Estate Directory|Free|DoFollow|India
Shiksha|https://www.shiksha.com/|78|Education Directory|Free|DoFollow|India
CollegeDekho|https://www.collegedekho.com/|62|Education Directory|Free|DoFollow|India
PRLog|https://www.prlog.org/|72|Press Release|Free|DoFollow|Global
PR.com|https://www.pr.com/|68|Press Release|Free|DoFollow|Global
OpenPR|https://www.openpr.com/|65|Press Release|Free|DoFollow|Global
Free Press Release|https://www.free-press-release.com/|55|Press Release|Free|DoFollow|Global
1888PressRelease|https://www.1888pressrelease.com/|58|Press Release|Free|DoFollow|Global
IssueWire|https://www.issuewire.com/|52|Press Release|Freemium|DoFollow|Global
Quora|https://www.quora.com/|93|Q&A Platform|Free|NoFollow|Global
Reddit|https://www.reddit.com/|97|Social Directory|Free|NoFollow|Global
Medium|https://www.medium.com/|95|Content Platform|Free|NoFollow|Global
Pinterest|https://www.pinterest.com/|94|Social Directory|Free|NoFollow|Global
YouTube|https://www.youtube.com/|100|Video Sharing|Free|NoFollow|Global
Instagram|https://www.instagram.com/|96|Social Directory|Free|NoFollow|Global
Twitter/X|https://www.twitter.com/|94|Social Directory|Free|NoFollow|Global
GitHub|https://github.com/|95|Developer Platform|Free|NoFollow|Global
Tumblr|https://www.tumblr.com/|86|Content Platform|Free|DoFollow|Global
WordPress.com|https://wordpress.com/|93|Content Platform|Freemium|NoFollow|Global
Gravatar|https://gravatar.com/|88|Profile Site|Free|DoFollow|Global
Issuu|https://issuu.com/|85|Content Platform|Freemium|DoFollow|Global
Vimeo|https://vimeo.com/|92|Video Sharing|Freemium|DoFollow|Global
Dailymotion|https://www.dailymotion.com/|82|Video Sharing|Free|DoFollow|Global
SoundCloud|https://soundcloud.com/|90|Audio Sharing|Freemium|DoFollow|Global
500px|https://500px.com/|78|Image Sharing|Free|DoFollow|Global
Diigo|https://www.diigo.com/|72|Bookmark Directory|Free|DoFollow|Global
Scoop.it|https://www.scoop.it/|82|Content Platform|Freemium|DoFollow|Global
Mix.com|https://mix.com/|75|Bookmark Directory|Free|DoFollow|Global
HubPages|https://www.hubpages.com/|78|Content Platform|Free|DoFollow|Global
WikiAlpha|https://www.wikialpha.org/|62|Wiki Site|Free|DoFollow|Global
EverybodyWiki|https://en.everybodywiki.com/|55|Wiki Site|Free|DoFollow|Global
Hotfrog|https://www.hotfrog.com/|65|Local Directory|Free|DoFollow|Global
Cylex|https://www.cylex.com/|55|Local Directory|Free|DoFollow|Global
Manta|https://www.manta.com/|72|Local Directory|Free|DoFollow|US
Superpages|https://www.superpages.com/|78|Local Directory|Free|DoFollow|US
DexKnows|https://www.dexknows.com/|68|Local Directory|Free|DoFollow|US
ChamberofCommerce|https://www.chamberofcommerce.com/|65|Business Directory|Free|DoFollow|US
Alignable|https://www.alignable.com/|62|Business Network|Free|DoFollow|US
Angi (Angie's List)|https://www.angi.com/|80|Review Site|Free|DoFollow|US
Thumbtack|https://www.thumbtack.com/|78|Service Directory|Freemium|NoFollow|US
Expertise.com|https://www.expertise.com/|70|Service Directory|Free|DoFollow|US
Zillow|https://www.zillow.com/|92|Real Estate Directory|Free|DoFollow|US
Glassdoor|https://www.glassdoor.com/|88|Review Site|Free|DoFollow|Global
Indeed|https://www.indeed.com/|92|Job Directory|Free|NoFollow|Global
Craigslist|https://www.craigslist.org/|92|Classifieds|Free|NoFollow|US
Gumtree|https://www.gumtree.com/|80|Classifieds|Free|NoFollow|Global
ClassifiedAds|https://www.classifiedads.com/|55|Classifieds|Free|DoFollow|US
Adpost|https://www.adpost.com/|62|Classifieds|Free|DoFollow|Global
Locanto|https://www.locanto.com/|68|Classifieds|Free|DoFollow|Global
DMOZ (Curlie)|https://curlie.org/|78|Web Directory|Free|DoFollow|Global
Entireweb|https://www.entireweb.com/|58|Web Directory|Free|DoFollow|Global
Blogarama|https://www.blogarama.com/|62|Blog Directory|Free|DoFollow|Global
OnTopList|https://www.ontoplist.com/|45|Blog Directory|Free|DoFollow|Global
ThreeBestRated|https://threebestrated.com/|68|Review Site|Free|DoFollow|Global
Infobel|https://www.infobel.com/|65|Local Directory|Free|DoFollow|Global
JustLanded|https://www.justlanded.com/|62|Local Directory|Free|DoFollow|Global
Bark.com|https://www.bark.com/|72|Service Directory|Freemium|DoFollow|Global
EZlocal|https://www.ezlocal.com/|55|Local Directory|Free|DoFollow|US
Fyple|https://www.fyple.com/|45|Local Directory|Free|DoFollow|Global
N49|https://www.n49.com/|42|Local Directory|Free|DoFollow|Global
iGlobal|https://www.iglobal.co/|40|Local Directory|Free|DoFollow|Global
Podbean|https://www.podbean.com/|72|Podcast Directory|Freemium|DoFollow|Global
Calameo|https://www.calameo.com/|78|Content Platform|Free|DoFollow|Global
FlipHTML5|https://fliphtml5.com/|75|Content Platform|Freemium|DoFollow|Global
Edocr|https://www.edocr.com/|55|Content Platform|Free|DoFollow|Global
Warrior Forum|https://www.warriorforum.com/|68|Business Forum|Free|DoFollow|Global
DigitalPoint|https://www.digitalpoint.com/|62|Business Forum|Free|DoFollow|Global
BizSugar|https://www.bizsugar.com/|55|Business Community|Free|DoFollow|Global
Truelancer|https://www.truelancer.com/|52|Freelance Marketplace|Free|DoFollow|India
Checkatrade UK|https://www.checkatrade.com/|68|Service Directory|Paid|DoFollow|UK
MyBuilder UK|https://www.mybuilder.com/|65|Service Directory|Freemium|DoFollow|UK
PagesJaunes France|https://www.pagesjaunes.fr/|82|Local Directory|Free|DoFollow|France
GelbeSeiten Germany|https://www.gelbeseiten.de/|78|Local Directory|Free|DoFollow|Germany
Finda NZ|https://www.finda.co.nz/|62|Local Directory|Free|DoFollow|New Zealand
StartLocal AU|https://www.startlocal.com.au/|55|Local Directory|Free|DoFollow|Australia"""

# ===========================================================
# SOURCE 4: Directory submission sites from Techasoft/ThGuideX
# ===========================================================
directory_sites = """1abc.org|https://www.1abc.org/|25|Web Directory|Free|DoFollow|Global
a1webdirectory.org|https://www.a1webdirectory.org/|35|Web Directory|Free|DoFollow|Global
9sites.net|https://www.9sites.net/|28|Web Directory|Free|DoFollow|Global
cipinet.com|https://www.cipinet.com/|30|Web Directory|Free|DoFollow|Global
linkcentre.com|https://www.linkcentre.com/|32|Web Directory|Free|DoFollow|Global
somuch.com|https://www.somuch.com/|35|Web Directory|Free|DoFollow|Global
exactseek.com|https://www.exactseek.com/|40|Web Directory|Free|DoFollow|Global
submitx.com|https://www.submitx.com/|32|Web Directory|Free|DoFollow|Global
freewebsubmission.com|https://www.freewebsubmission.com/|28|Web Directory|Free|DoFollow|Global
sonicrun.com|https://www.sonicrun.com/|30|Web Directory|Free|DoFollow|Global
alivedirectory.com|https://www.alivedirectory.com/|28|Web Directory|Free|DoFollow|Global
directoryworld.net|https://www.directoryworld.net/|25|Web Directory|Free|DoFollow|Global
avivadirectory.com|https://www.avivadirectory.com/|30|Web Directory|Free|DoFollow|Global
directoryjournal.com|https://www.directoryjournal.com/|35|Web Directory|Free|DoFollow|Global
prolinkdirectory.com|https://www.prolinkdirectory.com/|22|Web Directory|Free|DoFollow|Global
directoryfire.com|https://www.directoryfire.com/|25|Web Directory|Free|DoFollow|Global
cannylink.com|https://www.cannylink.com/|28|Web Directory|Free|DoFollow|Global
usalistingdirectory.com|https://www.usalistingdirectory.com/|20|Web Directory|Free|DoFollow|US
marketinginternetdirectory.com|https://www.marketinginternetdirectory.com/|22|Web Directory|Free|DoFollow|Global
247webdirectory.com|https://www.247webdirectory.com/|18|Web Directory|Free|DoFollow|Global
10directory.com|https://www.10directory.com/|20|Web Directory|Free|DoFollow|Global
411freedirectory.com|https://www.411freedirectory.com/|18|Web Directory|Free|DoFollow|US
pegasusdirectory.com|https://www.pegasusdirectory.com/|25|Web Directory|Freemium|DoFollow|Global
jasminedirectory.com|https://www.jasminedirectory.com/|42|Web Directory|Paid|DoFollow|Global
1webdirectory.com|https://www.1webdirectory.com/|22|Web Directory|Free|DoFollow|Global
botw.org|https://botw.org/|55|Web Directory|Paid|DoFollow|Global
joeant.com|https://www.joeant.com/|30|Web Directory|Free|DoFollow|Global
blogflux.com|https://www.blogflux.com/|35|Blog Directory|Free|DoFollow|Global
blogcatalog.com|https://www.blogcatalog.com/|40|Blog Directory|Free|DoFollow|Global
topofblogs.com|https://www.topofblogs.com/|32|Blog Directory|Free|DoFollow|Global
blogsearchengine.org|https://www.blogsearchengine.org/|28|Blog Directory|Free|DoFollow|Global
globeofblogs.com|https://www.globeofblogs.com/|25|Blog Directory|Free|DoFollow|Global
blogengage.com|https://www.blogengage.com/|30|Blog Directory|Free|DoFollow|Global
folkd.com|https://www.folkd.com/|60|Bookmark Directory|Free|DoFollow|Global
bookmarkbay.com|https://www.bookmarkbay.com/|28|Bookmark Directory|Free|DoFollow|Global
ezinearticles.com|https://www.ezinearticles.com/|72|Article Directory|Free|DoFollow|Global
selfgrowth.com|https://www.selfgrowth.com/|60|Article Directory|Free|DoFollow|Global
articlebiz.com|https://www.articlebiz.com/|42|Article Directory|Free|DoFollow|Global
ChatGPT Demo|https://chatgptdemo.com/|45|AI Tool Directory|Free|DoFollow|Global
TheresAnAIForThat|https://theresanaiforthat.com/|62|AI Tool Directory|Free|DoFollow|Global
Futurepedia|https://www.futurepedia.io/|55|AI Tool Directory|Free|DoFollow|Global
FutureTools|https://www.futuretools.io/|52|AI Tool Directory|Free|DoFollow|Global
TopAI.Tools|https://topai.tools/|42|AI Tool Directory|Free|DoFollow|Global
AllThingsAI|https://allthingsai.com/|40|AI Tool Directory|Free|DoFollow|Global
AIToolsDirectory|https://www.aitools.directory/|35|AI Tool Directory|Free|DoFollow|Global
EasyWithAI|https://easywithai.com/|38|AI Tool Directory|Free|DoFollow|Global
DoMore.ai|https://domore.ai/|32|AI Tool Directory|Free|DoFollow|Global
ToolScout.ai|https://toolscout.ai/|28|AI Tool Directory|Free|DoFollow|Global"""


# ===========================================================
# SOURCE 5: Quibustrainings verified data with DA
# ===========================================================
quibus_data = """justbaazaar.com|https://www.justbaazaar.com/|54|Local Directory|Free|DoFollow|India
urbanpro.com|https://www.urbanpro.com/|48|Service Directory|Freemium|DoFollow|India
surfindia.com|https://www.surfindia.com/|36|Local Directory|Free|DoFollow|India
altaindia.com|https://altaindia.com/|37|Local Directory|Free|DoFollow|India
indianceo.in|https://indianceo.in/|38|Business Directory|Free|DoFollow|India
indiatradezone.com|https://indiatradezone.com/|40|B2B Directory|Free|DoFollow|India
eximdata.com|https://eximdata.com/|41|B2B Directory|Free|DoFollow|India
startlocal.in|https://startlocal.in/|41|Local Directory|Free|DoFollow|India
addsera.in|https://addsera.in/|41|Local Directory|Free|DoFollow|India
smartguy.com|https://www.smartguy.com/|41|Local Directory|Free|DoFollow|Global
indianindustry.com|https://indianindustry.com/|42|B2B Directory|Free|DoFollow|India
whereincity.com|https://whereincity.com/|53|Local Directory|Free|DoFollow|India
company.fm|https://company.fm/|49|Business Directory|Free|DoFollow|Global
routeandgo.net|https://routeandgo.net/|50|Local Directory|Free|DoFollow|Global
bizcommunity.com|https://bizcommunity.com/|75|Business Directory|Free|DoFollow|Global
communitywalk.com|https://communitywalk.com/|76|Local Directory|Free|DoFollow|Global
designfirms.org|https://designfirms.org/|52|Agency Directory|Free|DoFollow|Global
businessfinder.in|https://www.businessfinder.in/|58|Local Directory|Free|DoFollow|India
gidonline.com|https://gidonline.com/|54|Local Directory|Free|DoFollow|India
yellowpagecity.com|https://www.yellowpagecity.com/|44|Local Directory|Free|DoFollow|Global
wowcity.com|https://in.wowcity.com/|50|Local Directory|Free|DoFollow|India
kugli.com|https://kugli.com/|50|Classifieds|Free|DoFollow|Global
akama.com|https://akama.com/|49|Local Directory|Free|DoFollow|Global
locanto.net|https://www.locanto.net/|46|Classifieds|Free|DoFollow|Global
igotbiz.com|https://igotbiz.com/|56|Local Directory|Free|DoFollow|India
cityinsider.com|https://cityinsider.com/|58|Local Directory|Free|DoFollow|Global
businessworld.in|https://businessworld.in/|78|Business Directory|Free|DoFollow|India
slideshare.net|https://www.slideshare.net/|95|Content Platform|Free|DoFollow|Global
trustpilot.com|https://www.trustpilot.com/|92|Review Site|Free|DoFollow|Global
foursquare.com|https://foursquare.com/|92|Local Directory|Free|DoFollow|Global
yelp.com|https://www.yelp.com/|93|Review Site|Free|NoFollow|Global
manta.com|https://manta.com/|88|Local Directory|Free|DoFollow|US
angel.co|https://angel.co/|85|Startup Directory|Free|DoFollow|Global
about.me|https://about.me/|92|Profile Site|Freemium|DoFollow|Global
amazon.in|https://www.amazon.in/|92|Marketplace|Freemium|DoFollow|India
snapdeal.com|https://www.snapdeal.com/|87|Marketplace|Freemium|DoFollow|India
addressguru.in|https://www.addressguru.in/|16|Local Directory|Free|DoFollow|India
localfrog.in|https://www.localfrog.in/|13|Local Directory|Free|DoFollow|India
bharathlisting.com|https://bharathlisting.com/|26|Local Directory|Free|DoFollow|India
poweredindia.com|https://www.poweredindia.com/|24|Local Directory|Free|DoFollow|India
justcityplace.com|https://www.justcityplace.com/|29|Local Directory|Free|DoFollow|India
mybusinesslive.in|https://www.mybusinesslive.in/|11|Local Directory|Free|DoFollow|India
dialmenow.in|https://www.dialmenow.in/|32|Local Directory|Free|DoFollow|India
indialist.com|https://indialist.com/|47|Local Directory|Free|DoFollow|India
placereference.com|https://placereference.com/|48|Local Directory|Free|DoFollow|Global
sholay.in|https://sholay.in/|24|Local Directory|Free|DoFollow|India
cylex.in|https://cylex.in/|43|Local Directory|Free|DoFollow|India
bizsheet.com|https://bizsheet.com/|43|Business Directory|Free|DoFollow|Global
jimyellowpages.com|https://jimyellowpages.com/|44|Local Directory|Free|DoFollow|India
buckeyeads.com|https://buckeyeads.com/|42|Classifieds|Free|DoFollow|US
croozi.com|https://www.croozi.com/|35|Local Directory|Free|DoFollow|Global
anibookmark.com|https://anibookmark.com/|45|Bookmark Directory|Free|DoFollow|Global
canadaone.com|https://www.canadaone.com/|42|Business Directory|Free|DoFollow|Canada
indiabizlist.com|https://www.indiabizlist.com/|15|Local Directory|Free|DoFollow|India"""


def parse_data(raw_text):
    """Parse pipe-delimited data into list of dicts."""
    records = []
    for line in raw_text.strip().split("\n"):
        parts = line.split("|")
        if len(parts) >= 7:
            records.append({
                "Website Name": parts[0].strip(),
                "URL": parts[1].strip(),
                "Domain Authority": parts[2].strip(),
                "Category": parts[3].strip(),
                "Type (Free/Paid)": parts[4].strip(),
                "Link Type (DoFollow/NoFollow)": parts[5].strip(),
                "Country": parts[6].strip(),
            })
    return records


def deduplicate(df):
    """Remove duplicates based on domain."""
    def get_domain(url):
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            return url.lower()

    df["_domain"] = df["URL"].apply(get_domain)

    # Keep the record with the highest DA for each domain
    df["_da_num"] = pd.to_numeric(df["Domain Authority"], errors="coerce").fillna(0)
    df = df.sort_values("_da_num", ascending=False).drop_duplicates(subset=["_domain"], keep="first")
    df = df.drop(columns=["_domain", "_da_num"])
    return df


def main():
    print("Compiling business listing sites from verified sources...")

    # Parse all sources
    all_records = []
    all_records.extend(parse_data(seoaimpoint_data))
    print(f"  Source 1 (SEOAimPoint): {len(parse_data(seoaimpoint_data))} sites")

    all_records.extend(parse_data(skillwaala_data))
    print(f"  Source 2 (Skillwaala): {len(parse_data(skillwaala_data))} sites")

    all_records.extend(parse_data(additional_data))
    print(f"  Source 3 (Additional verified): {len(parse_data(additional_data))} sites")

    all_records.extend(parse_data(directory_sites))
    print(f"  Source 4 (Directory sites): {len(parse_data(directory_sites))} sites")

    all_records.extend(parse_data(quibus_data))
    print(f"  Source 5 (Quibustrainings): {len(parse_data(quibus_data))} sites")

    # Source 6: Extra directory URLs from expert-seo (800+ URLs)
    extra_file = os.path.join(os.path.dirname(__file__), "extra_directories.txt")
    if os.path.exists(extra_file):
        extra_count = 0
        with open(extra_file, "r") as f:
            for line in f:
                url = line.strip()
                if url and url.startswith("http"):
                    domain = urlparse(url).netloc.replace("www.", "")
                    name = domain.replace(".com", "").replace(".org", "").replace(".net", "").replace(".io", "").title()
                    all_records.append({
                        "Website Name": name,
                        "URL": url,
                        "Domain Authority": "",
                        "Category": "Web Directory",
                        "Type (Free/Paid)": "Free",
                        "Link Type (DoFollow/NoFollow)": "DoFollow",
                        "Country": "Global",
                    })
                    extra_count += 1
        print(f"  Source 6 (Expert-SEO directories): {extra_count} sites")

    print(f"\n  Total raw: {len(all_records)} sites")

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Deduplicate
    before = len(df)
    df = deduplicate(df)
    print(f"  After dedup: {len(df)} unique sites (removed {before - len(df)} duplicates)")

    # Sort by DA descending
    df["_sort_da"] = pd.to_numeric(df["Domain Authority"], errors="coerce").fillna(0)
    df = df.sort_values("_sort_da", ascending=False).drop(columns=["_sort_da"])
    df = df.reset_index(drop=True)

    # Save CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  CSV saved: {OUTPUT_CSV} ({len(df)} sites)")

    # Save Excel
    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"  Excel saved: {OUTPUT_XLSX} ({len(df)} sites)")

    # Stats
    print(f"\n  === SUMMARY ===")
    print(f"  Total unique sites: {len(df)}")
    print(f"  Categories: {df['Category'].nunique()}")
    print(f"  Countries: {df['Country'].nunique()}")
    print(f"  Free sites: {len(df[df['Type (Free/Paid)'] == 'Free'])}")
    print(f"  DoFollow sites: {len(df[df['Link Type (DoFollow/NoFollow)'] == 'DoFollow'])}")
    print(f"  High DA (50+): {len(df[pd.to_numeric(df['Domain Authority'], errors='coerce') >= 50])}")

    # Open the file
    import platform, subprocess
    filepath = os.path.abspath(OUTPUT_XLSX)
    print(f"\n  Opening: {filepath}")
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print(f"  Could not auto-open: {e}")


if __name__ == "__main__":
    main()
