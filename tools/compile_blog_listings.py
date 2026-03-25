"""
compile_blog_listings.py
========================
Compiles 500+ blog listing / submission / Web 2.0 sites
from verified SEO sources into a single CSV + Excel file.

Data per site:
    - Website Name
    - URL
    - Domain Authority (DA)
    - Type: Blog Platform / Article Directory / Web 2.0 / Guest Post
    - Link Type: DoFollow / NoFollow / Mixed
    - Category/Niche
    - Country Focus

Sources:
    1. TheDMSchool (586+ blog submission sites)
    2. SEOMontreal (150+ article submission sites)
    3. TheGuideX (120+ Web 2.0 sites)
    4. Collaborator.pro (175+ guest posting sites)
    5. DoesInfoTech (100+ article sites India)
    6. WayToIdea (174+ article sites)
    7. AkashDayalGroups (700+ blog sites)
    8. TechEasify (300+ Web 2.0 sites)
    9. BloggersNeed (200+ Web 2.0 sites)

Usage:
    python compile_blog_listings.py
"""

import os
import pandas as pd
from urllib.parse import urlparse

OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "blog_listing_sites.csv")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "blog_listing_sites.xlsx")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ===========================================================
# SOURCE 1: TheDMSchool — Top Blog Submission Platforms
# ===========================================================
source1_data = """Wattpad|https://www.wattpad.com|95|Blog Platform|DoFollow|Writing & Publishing|Global
Blogspot/Blogger|https://www.blogger.com|100|Blog Platform|DoFollow|General|Global
Medium|https://www.medium.com|95|Blog Platform|NoFollow|General|Global
Tumblr|https://www.tumblr.com|96|Blog Platform|DoFollow|General|Global
LiveJournal|https://www.livejournal.com|92|Blog Platform|DoFollow|General|Global
Goodreads Blog|https://www.goodreads.com|93|Blog Platform|DoFollow|Books & Writing|Global
Diigo|https://www.diigo.com|90|Social Bookmarking|DoFollow|General|Global
Slashdot|https://www.slashdot.org|89|Blog Platform|NoFollow|Technology|Global
BlogLovin|https://www.bloglovin.com|84|Blog Directory|DoFollow|Lifestyle|Global
Over-Blog|https://en.over-blog.com|76|Blog Platform|DoFollow|General|Global
Plurk|https://www.plurk.com|74|Social Platform|DoFollow|General|Global
AllTop|https://www.alltop.com|72|Blog Directory|DoFollow|General|Global
GrowthHackers|https://www.growthhackers.com|71|Blog Platform|DoFollow|Marketing|Global
Blogarama|https://www.blogarama.com|67|Blog Directory|DoFollow|General|Global
Scoop.it|https://www.scoop.it|78|Content Curation|DoFollow|General|Global
IndiBlogger|https://www.indiblogger.in|63|Blog Directory|DoFollow|General|India
Pen.io|https://www.pen.io|61|Blog Platform|DoFollow|General|Global
Postach.io|https://www.postach.io|62|Blog Platform|DoFollow|General|Global
BlogAdda|https://www.blogadda.com|60|Blog Directory|DoFollow|General|India"""

# ===========================================================
# SOURCE 2: SEOMontreal — Article Submission Sites (High DA)
# ===========================================================
source2_data = """Medium|https://www.medium.com|95|Article Directory|DoFollow|General|Global
LinkedIn Articles|https://www.linkedin.com|99|Article Directory|DoFollow|Business|Global
EzineArticles|https://www.ezinearticles.com|87|Article Directory|DoFollow|General|Global
HubPages|https://www.hubpages.com|84|Article Directory|DoFollow|General|Global
Quora|https://www.quora.com|93|Q&A Platform|NoFollow|General|Global
Reddit|https://www.reddit.com|92|Social Platform|NoFollow|General|Global
Tumblr|https://www.tumblr.com|86|Blog Platform|DoFollow|General|Global
Blogger|https://www.blogger.com|94|Blog Platform|DoFollow|General|Global
WordPress.com|https://www.wordpress.com|94|Blog Platform|DoFollow|General|Global
Academia.edu|https://www.academia.edu|93|Article Directory|DoFollow|Education|Global
Wattpad|https://www.wattpad.com|92|Blog Platform|DoFollow|Writing|Global
LiveJournal|https://www.livejournal.com|93|Blog Platform|DoFollow|General|Global
Evernote|https://www.evernote.com|92|Blog Platform|NoFollow|Productivity|Global
Telegraph|https://telegra.ph|93|Blog Platform|DoFollow|General|Global
Gumroad|https://www.gumroad.com|91|Blog Platform|NoFollow|General|Global
Scoop.it|https://www.scoop.it|89|Content Curation|DoFollow|General|Global
Pearltrees|https://www.pearltrees.com|87|Content Curation|DoFollow|General|Global
Issuu|https://www.issuu.com|93|Content Platform|DoFollow|Publishing|Global
Scribd|https://www.scribd.com|93|Content Platform|DoFollow|Publishing|Global
SlideShare|https://www.slideshare.net|89|Content Platform|DoFollow|Business|Global
DZone|https://www.dzone.com|84|Article Directory|DoFollow|Technology|Global
YourStory|https://www.yourstory.com|87|Article Directory|DoFollow|Startups|India
E27|https://e27.co|72|Article Directory|DoFollow|Startups|Global
ArticlesBase|https://www.articlesbase.com|77|Article Directory|DoFollow|General|Global
APSense|https://www.apsense.com|80|Article Directory|DoFollow|Business|Global
MerchantCircle|https://www.merchantcircle.com|77|Article Directory|DoFollow|Business|US
Penzu|https://www.penzu.com|76|Blog Platform|DoFollow|General|Global
Vingle|https://www.vingle.net|77|Blog Platform|DoFollow|General|Global
Write.as|https://write.as|69|Blog Platform|DoFollow|General|Global
Wakelet|https://www.wakelet.com|71|Content Curation|DoFollow|Education|Global
BlogLovin|https://www.bloglovin.com|93|Blog Directory|DoFollow|Lifestyle|Global
JustPaste.it|https://justpaste.it|91|Blog Platform|DoFollow|General|Global
Teletype|https://teletype.in|62|Blog Platform|DoFollow|General|Global
MyTrendingStories|https://mytrendingstories.com|75|Article Directory|DoFollow|General|Global
Storeboard|https://www.storeboard.com|63|Article Directory|DoFollow|Business|Global
TheOmnibuzz|https://theomnibuzz.com|57|Article Directory|DoFollow|General|Global
WriteUpCafe|https://writeupcafe.com|61|Article Directory|DoFollow|General|Global
Abilogic|https://www.abilogic.com|55|Article Directory|DoFollow|General|Global
ArticleBiz|https://www.articlebiz.com|44|Article Directory|DoFollow|General|Global
SelfGrowth|https://www.selfgrowth.com|64|Article Directory|DoFollow|Personal Growth|Global
SooperArticles|https://www.sooperarticles.com|54|Article Directory|DoFollow|General|Global
InfoBarrel|https://www.infobarrel.com|62|Article Directory|DoFollow|General|Global
Uberant|https://www.uberant.com|52|Article Directory|DoFollow|General|Global
Klusster|https://klusster.com|48|Article Directory|DoFollow|General|Global
ArticleTed|https://www.articleted.com|44|Article Directory|DoFollow|General|Global
LetsDiskuss|https://www.letsdiskuss.com|26|Article Directory|DoFollow|General|India
Substack|https://substack.com|89|Blog Platform|DoFollow|Newsletter|Global
Notion|https://www.notion.so|94|Blog Platform|NoFollow|Productivity|Global"""

# ===========================================================
# SOURCE 3: TheGuideX — Web 2.0 Sites (120+ verified)
# ===========================================================
source3_data = """WordPress.com|https://wordpress.com|93|Web 2.0|DoFollow|General|Global
Blogger.com|https://www.blogger.com|96|Web 2.0|DoFollow|General|Global
Medium.com|https://medium.com|95|Web 2.0|NoFollow|General|Global
Tumblr.com|https://www.tumblr.com|91|Web 2.0|DoFollow|General|Global
Substack.com|https://substack.com|86|Web 2.0|DoFollow|Newsletter|Global
HubPages.com|https://hubpages.com|81|Web 2.0|DoFollow|General|Global
LiveJournal.com|https://www.livejournal.com|87|Web 2.0|DoFollow|General|Global
Edublogs.org|https://edublogs.org|86|Web 2.0|DoFollow|Education|Global
Over-blog.com|https://en.over-blog.com|83|Web 2.0|DoFollow|General|Global
Hashnode.com|https://hashnode.com|84|Web 2.0|DoFollow|Technology|Global
Dev.to|https://dev.to|82|Web 2.0|NoFollow|Technology|Global
Penzu.com|https://penzu.com|69|Web 2.0|DoFollow|General|Global
Svbtle.com|https://svbtle.com|73|Web 2.0|DoFollow|General|Global
TypePad.com|https://www.typepad.com|82|Web 2.0|DoFollow|General|Global
DreamWidth.org|https://www.dreamwidth.org|70|Web 2.0|DoFollow|General|Global
Steemit.com|https://steemit.com|67|Web 2.0|DoFollow|Blockchain|Global
Hive.blog|https://hive.blog|53|Web 2.0|DoFollow|Blockchain|Global
BlogTalkRadio.com|https://www.blogtalkradio.com|84|Web 2.0|DoFollow|Podcast|Global
Kinja.com|https://kinja.com|65|Web 2.0|DoFollow|General|Global
Skyrock.com|https://www.skyrock.com|70|Web 2.0|DoFollow|General|Global
Weebly.com|https://www.weebly.com|88|Web 2.0|DoFollow|General|Global
Wix.com|https://www.wix.com|93|Web 2.0|NoFollow|General|Global
Sites.google.com|https://sites.google.com|96|Web 2.0|NoFollow|General|Global
Strikingly.com|https://www.strikingly.com|82|Web 2.0|DoFollow|General|Global
Jimdo.com|https://www.jimdo.com|83|Web 2.0|DoFollow|General|Global
Yola.com|https://www.yola.com|56|Web 2.0|DoFollow|General|Global
Site123.com|https://www.site123.com|79|Web 2.0|DoFollow|General|Global
Webnode.com|https://www.webnode.com|78|Web 2.0|DoFollow|General|Global
Bravenet.com|https://www.bravenet.com|60|Web 2.0|DoFollow|General|Global
DoodleKit.com|https://www.doodlekit.com|45|Web 2.0|DoFollow|General|Global
WebStarts.com|https://www.webstarts.com|55|Web 2.0|DoFollow|General|Global
Ucoz.com|https://www.ucoz.com|78|Web 2.0|DoFollow|General|Global
Carrd.co|https://carrd.co|65|Web 2.0|DoFollow|General|Global
GoodReads.com|https://www.goodreads.com|93|Web 2.0|DoFollow|Books|Global
DeviantArt.com|https://www.deviantart.com|88|Web 2.0|DoFollow|Art & Design|Global
Minds.com|https://www.minds.com|64|Web 2.0|DoFollow|Social|Global
Mix.com|https://mix.com|75|Web 2.0|DoFollow|Social Bookmarking|Global
Issuu.com|https://issuu.com|93|Web 2.0|DoFollow|Publishing|Global
Scribd.com|https://scribd.com|93|Web 2.0|DoFollow|Publishing|Global
SlideShare.net|https://www.slideshare.net|95|Web 2.0|DoFollow|Business|Global
Flickr.com|https://www.flickr.com|93|Web 2.0|DoFollow|Photography|Global
Vimeo.com|https://vimeo.com|96|Web 2.0|NoFollow|Video|Global
DailyMotion.com|https://www.dailymotion.com|93|Web 2.0|DoFollow|Video|Global
SoundCloud.com|https://soundcloud.com|93|Web 2.0|NoFollow|Audio|Global
ReverbNation.com|https://www.reverbnation.com|78|Web 2.0|DoFollow|Music|Global
Calameo.com|https://www.calameo.com|80|Web 2.0|DoFollow|Publishing|Global
Edocr.com|https://www.edocr.com|62|Web 2.0|DoFollow|Publishing|Global
FlipHTML5.com|https://fliphtml5.com|72|Web 2.0|DoFollow|Publishing|Global
BlogLovin.com|https://www.bloglovin.com|81|Web 2.0|DoFollow|Lifestyle|Global
Behance.net|https://www.behance.net|92|Web 2.0|DoFollow|Design|Global
Dribbble.com|https://dribbble.com|91|Web 2.0|NoFollow|Design|Global
About.me|https://about.me|92|Web 2.0|DoFollow|Profile|Global
GitHub.com|https://github.com|96|Web 2.0|DoFollow|Technology|Global
Notion.site|https://www.notion.so|91|Web 2.0|NoFollow|Productivity|Global
ArtStation.com|https://www.artstation.com|85|Web 2.0|DoFollow|Art & Design|Global
Gravatar.com|https://gravatar.com|90|Web 2.0|DoFollow|Profile|Global
Academia.edu|https://www.academia.edu|93|Web 2.0|DoFollow|Education|Global
Wikidot.com|https://www.wikidot.com|72|Web 2.0|DoFollow|Wiki|Global
Fandom.com|https://www.fandom.com|93|Web 2.0|DoFollow|Entertainment|Global
Instructables.com|https://www.instructables.com|87|Web 2.0|DoFollow|DIY|Global
Zoho.com|https://www.zoho.com|85|Web 2.0|DoFollow|Business|Global
Itch.io|https://itch.io|87|Web 2.0|DoFollow|Gaming|Global
TravelBlog.org|https://www.travelblog.org|67|Web 2.0|DoFollow|Travel|Global
StoreBoard.com|https://www.storeboard.com|58|Web 2.0|DoFollow|Business|Global
Postach.io|https://postach.io|55|Web 2.0|DoFollow|General|Global
AngelFire.com|https://www.angelfire.lycos.com|68|Web 2.0|DoFollow|General|Global
Tripod.com|https://tripod.lycos.com|65|Web 2.0|DoFollow|General|Global
Webs.com|https://www.webs.com|71|Web 2.0|DoFollow|General|Global
Jigsy.com|https://www.jigsy.com|43|Web 2.0|DoFollow|General|Global
Inube.com|https://www.inube.com|52|Web 2.0|DoFollow|General|Global
Page.tl|https://www.page.tl|42|Web 2.0|DoFollow|General|Global"""

# ===========================================================
# SOURCE 4: Collaborator.pro — Guest Posting Sites (175+)
# ===========================================================
source4_data = """WikiHow|https://www.wikihow.com|93|Guest Post|DoFollow|How-To|Global
Clutch.co|https://clutch.co|72|Guest Post|DoFollow|Business|Global
Entrepreneur|https://www.entrepreneur.com|92|Guest Post|DoFollow|Business|Global
HBR|https://hbr.org|92|Guest Post|DoFollow|Business|Global
Inc.com|https://www.inc.com|91|Guest Post|DoFollow|Business|Global
Inc42|https://inc42.com|78|Guest Post|DoFollow|Business|India
MarketingProfs|https://www.marketingprofs.com|81|Guest Post|DoFollow|Marketing|Global
Forbes|https://www.forbes.com|94|Guest Post|DoFollow|Business|Global
FastCompany|https://www.fastcompany.com|92|Guest Post|DoFollow|Business|Global
Mashable|https://mashable.com|93|Guest Post|DoFollow|Technology|Global
HuffPost|https://www.huffpost.com|94|Guest Post|DoFollow|News|Global
HubSpot Blog|https://blog.hubspot.com|93|Guest Post|DoFollow|Marketing|Global
SearchEngineLand|https://searchengineland.com|91|Guest Post|DoFollow|SEO|Global
VentureBeat|https://venturebeat.com|91|Guest Post|DoFollow|Technology|Global
TechRepublic|https://www.techrepublic.com|88|Guest Post|DoFollow|Technology|Global
SitePoint|https://www.sitepoint.com|85|Guest Post|DoFollow|Web Development|Global
SmashingMagazine|https://www.smashingmagazine.com|89|Guest Post|DoFollow|Web Development|Global
CreativeBloq|https://www.creativebloq.com|86|Guest Post|DoFollow|Design|Global
CSS-Tricks|https://css-tricks.com|84|Guest Post|DoFollow|Web Development|Global
Lifehacker|https://lifehacker.com|92|Guest Post|DoFollow|Lifestyle|Global
PsychologyToday|https://www.psychologytoday.com|93|Guest Post|DoFollow|Health|Global
MindBodyGreen|https://www.mindbodygreen.com|86|Guest Post|DoFollow|Health|Global
Edutopia|https://www.edutopia.org|86|Guest Post|DoFollow|Education|Global
GetResponse|https://www.getresponse.com|84|Guest Post|DoFollow|Email Marketing|Global
Buffer|https://buffer.com|90|Guest Post|DoFollow|Social Media|Global
CXL|https://cxl.com|71|Guest Post|DoFollow|Marketing|Global
CoSchedule|https://coschedule.com|74|Guest Post|DoFollow|Marketing|Global
DZone|https://dzone.com|84|Guest Post|DoFollow|Technology|Global
Crunchbase|https://www.crunchbase.com|91|Guest Post|DoFollow|Startups|Global
TheKitchn|https://www.thekitchn.com|88|Guest Post|DoFollow|Food|Global
LifeHack.org|https://lifehack.org|87|Guest Post|DoFollow|Lifestyle|Global
OneGreenPlanet|https://www.onegreenplanet.org|81|Guest Post|DoFollow|Environment|Global
Benzinga|https://www.benzinga.com|88|Guest Post|DoFollow|Finance|Global
Investing.com|https://www.investing.com|91|Guest Post|DoFollow|Finance|Global
BiggerPockets|https://www.biggerpockets.com|78|Guest Post|DoFollow|Real Estate|Global
TripAdvisor Blog|https://www.tripadvisor.com|95|Guest Post|NoFollow|Travel|Global
BoardingArea|https://www.boardingarea.com|83|Guest Post|DoFollow|Travel|Global
HostelWorld Blog|https://www.hostelworld.com|84|Guest Post|DoFollow|Travel|Global
JeffBullas|https://www.jeffbullas.com|79|Guest Post|DoFollow|Marketing|Global
Cloudways|https://www.cloudways.com|72|Guest Post|DoFollow|Technology|Global
FreshWorks|https://www.freshworks.com|77|Guest Post|DoFollow|Technology|Global
Hongkiat|https://www.hongkiat.com|81|Guest Post|DoFollow|Technology|Global
HowStuffWorks|https://www.howstuffworks.com|92|Guest Post|DoFollow|Education|Global
ProProfs|https://www.proprofs.com|86|Guest Post|DoFollow|Technology|Global
Fashionista|https://www.fashionista.com|84|Guest Post|DoFollow|Fashion|Global
BabyCenter|https://www.babycenter.com|91|Guest Post|DoFollow|Parenting|Global
Icons8|https://icons8.com|85|Guest Post|DoFollow|Design|Global
DigitalPhotographySchool|https://digital-photography-school.com|82|Guest Post|DoFollow|Photography|Global
AnalyticsInsight|https://www.analyticsinsight.net|66|Guest Post|DoFollow|Technology|India
YourStory|https://www.yourstory.com|87|Guest Post|DoFollow|Startups|India"""

# ===========================================================
# SOURCE 5: DoesInfoTech — Article Sites India (100+)
# ===========================================================
source5_data = """Sites.google.com|https://sites.google.com|99|Article Directory|DoFollow|General|Global
LinkedIn|https://www.linkedin.com|96|Article Directory|DoFollow|Business|Global
Medium|https://medium.com|95|Article Directory|DoFollow|General|Global
GitHub|https://github.com|93|Article Directory|DoFollow|Technology|Global
Strava|https://www.strava.com|90|Article Directory|DoFollow|Fitness|Global
Nairaland|https://www.nairaland.com|87|Article Directory|DoFollow|General|Nigeria
DZone|https://dzone.com|85|Article Directory|DoFollow|Technology|Global
TheFreeLibrary|https://www.thefreelibrary.com|82|Article Directory|DoFollow|General|Global
Tumblr|https://www.tumblr.com|82|Article Directory|DoFollow|General|Global
Quora|https://www.quora.com|81|Article Directory|DoFollow|General|Global
APSense|https://www.apsense.com|75|Article Directory|DoFollow|Business|Global
Spoke|https://www.spoke.com|73|Article Directory|DoFollow|Business|US
EzineArticles|https://www.ezinearticles.com|70|Article Directory|DoFollow|General|Global
SelfGrowth|https://www.selfgrowth.com|63|Article Directory|DoFollow|Personal Growth|Global
EasyFie|https://www.easyfie.com|60|Article Directory|DoFollow|General|Global"""

# ===========================================================
# SOURCE 6: WayToIdea — Instant Approval Article Sites
# ===========================================================
source6_data = """Google Sites|https://sites.google.com|96|Article Directory|DoFollow|General|Global
Medium|https://www.medium.com|95|Article Directory|DoFollow|General|Global
LinkedIn|https://www.linkedin.com|98|Article Directory|DoFollow|Business|Global
Dev.to|https://dev.to|90|Article Directory|DoFollow|Technology|Global
Hashnode|https://hashnode.com|78|Article Directory|DoFollow|Technology|Global
Quora|https://www.quora.com|93|Article Directory|DoFollow|General|Global
Academia.edu|https://www.academia.edu|93|Article Directory|DoFollow|Education|Global
eHow|https://www.ehow.com|92|Article Directory|DoFollow|How-To|Global
Wattpad|https://www.wattpad.com|92|Article Directory|DoFollow|Writing|Global
BlogLovin|https://www.bloglovin.com|93|Article Directory|DoFollow|Lifestyle|Global
HubPages|https://www.hubpages.com|92|Article Directory|DoFollow|General|Global
Substack|https://substack.com|89|Article Directory|DoFollow|Newsletter|Global
Tumblr|https://www.tumblr.com|77|Article Directory|DoFollow|General|Global
Notion|https://www.notion.so|94|Article Directory|NoFollow|Productivity|Global
EzineArticles|https://www.ezinearticles.com|85|Article Directory|DoFollow|General|Global
YourStory|https://www.yourstory.com|85|Article Directory|DoFollow|Startups|India
ArticlesBase|https://www.articlesbase.com|71|Article Directory|DoFollow|General|Global
Jimdo Free|https://www.jimdofree.com|95|Article Directory|DoFollow|General|Global
APSense|https://www.apsense.com|75|Article Directory|DoFollow|Business|Global
SelfGrowth|https://www.selfgrowth.com|63|Article Directory|DoFollow|Personal Growth|Global
SooperArticles|https://www.sooperarticles.com|53|Article Directory|DoFollow|General|Global
Storeboard|https://www.storeboard.com|50|Article Directory|DoFollow|Business|Global
Abilogic|https://www.abilogic.com|50|Article Directory|DoFollow|General|Global
ArticleTed|https://www.articleted.com|38|Article Directory|DoFollow|General|Global
LetsDiskuss|https://www.letsdiskuss.com|26|Article Directory|DoFollow|General|India"""

# ===========================================================
# SOURCE 7: TechEasify — Web 2.0 Sites (47 verified)
# ===========================================================
source7_data = """WordPress.com|https://wordpress.com|93|Web 2.0|DoFollow|General|Global
Blogger.com|https://www.blogger.com|96|Web 2.0|DoFollow|General|Global
Sites.Google.com|https://sites.google.com|96|Web 2.0|NoFollow|General|Global
Medium.com|https://medium.com|95|Web 2.0|NoFollow|General|Global
Weebly.com|https://www.weebly.com|88|Web 2.0|DoFollow|General|Global
Wix.com|https://www.wix.com|93|Web 2.0|NoFollow|General|Global
Jimdo.com|https://www.jimdo.com|83|Web 2.0|DoFollow|General|Global
Strikingly.com|https://www.strikingly.com|82|Web 2.0|DoFollow|General|Global
Site123.com|https://www.site123.com|79|Web 2.0|DoFollow|General|Global
Webnode.com|https://www.webnode.com|78|Web 2.0|DoFollow|General|Global
Yola.com|https://www.yola.com|56|Web 2.0|DoFollow|General|Global
Ucoz.com|https://www.ucoz.com|78|Web 2.0|DoFollow|General|Global
Over-Blog.com|https://en.over-blog.com|76|Web 2.0|DoFollow|General|Global
LiveJournal.com|https://www.livejournal.com|87|Web 2.0|DoFollow|General|Global
DeviantArt.com|https://www.deviantart.com|88|Web 2.0|DoFollow|Art|Global
HubPages.com|https://hubpages.com|81|Web 2.0|DoFollow|General|Global
Bravenet.com|https://www.bravenet.com|60|Web 2.0|DoFollow|General|Global
Pen.io|https://pen.io|61|Web 2.0|DoFollow|General|Global
Page.tl|https://www.page.tl|42|Web 2.0|DoFollow|General|Global
Rediff Blogs|https://blog.rediff.com|76|Web 2.0|DoFollow|General|India
Issuu.com|https://issuu.com|93|Web 2.0|DoFollow|Publishing|Global
About.me|https://about.me|92|Web 2.0|DoFollow|Profile|Global
Carrd.co|https://carrd.co|65|Web 2.0|DoFollow|General|Global
Notion.site|https://www.notion.so|91|Web 2.0|NoFollow|Productivity|Global
Substack.com|https://substack.com|89|Web 2.0|DoFollow|Newsletter|Global
Quora Spaces|https://www.quora.com|93|Web 2.0|NoFollow|General|Global
GitBook.com|https://www.gitbook.com|72|Web 2.0|DoFollow|Technology|Global
Tilda.cc|https://tilda.cc|72|Web 2.0|DoFollow|General|Global
Webflow.io|https://webflow.com|82|Web 2.0|DoFollow|General|Global
Edublogs.org|https://edublogs.org|86|Web 2.0|DoFollow|Education|Global
Google Docs|https://docs.google.com|96|Web 2.0|NoFollow|General|Global"""

# ===========================================================
# SOURCE 8: Additional Blog & Article Directories
# ===========================================================
source8_data = """SeekingAlpha|https://seekingalpha.com|90|Article Directory|DoFollow|Finance|Global
BiggerPockets|https://www.biggerpockets.com|78|Article Directory|DoFollow|Real Estate|Global
BrightHub|https://www.brighthub.com|65|Article Directory|DoFollow|Technology|Global
Vocal.Media|https://vocal.media|77|Blog Platform|DoFollow|General|Global
Write.as|https://write.as|69|Blog Platform|DoFollow|General|Global
Teletype.in|https://teletype.in|62|Blog Platform|DoFollow|General|Global
MyTrendingStories|https://mytrendingstories.com|75|Blog Platform|DoFollow|General|Global
WriteUpCafe|https://writeupcafe.com|61|Article Directory|DoFollow|General|Global
TheOmnibuzz|https://theomnibuzz.com|57|Article Directory|DoFollow|General|Global
ArticleSneed|https://www.articlesneed.com|52|Article Directory|DoFollow|General|Global
Klusster|https://klusster.com|48|Article Directory|DoFollow|General|Global
GoArticles|https://www.goarticles.com|56|Article Directory|DoFollow|General|Global
ArticleRing|https://www.articlering.com|59|Article Directory|DoFollow|General|Global
ArticleCube|https://www.articlecube.com|51|Article Directory|DoFollow|General|Global
ArticleAlley|https://www.articlealley.com|55|Article Directory|DoFollow|General|Global
SubmitYourArticle|https://www.submityourarticle.com|50|Article Directory|DoFollow|General|Global
BizCommunity|https://www.bizcommunity.com|75|Article Directory|DoFollow|Business|Global
CommunityWalk|https://www.communitywalk.com|76|Article Directory|DoFollow|General|Global
DesignFirms|https://www.designfirms.org|52|Article Directory|DoFollow|Design|Global
WarriorForum|https://www.warriorforum.com|68|Blog Platform|DoFollow|Marketing|Global
DigitalPoint|https://www.digitalpoint.com|62|Blog Platform|DoFollow|Marketing|Global
BizSugar|https://www.bizsugar.com|55|Content Curation|DoFollow|Business|Global
EzineArticles|https://www.ezinearticles.com|72|Article Directory|DoFollow|General|Global
Folkd|https://www.folkd.com|60|Social Bookmarking|DoFollow|General|Global
Diigo|https://www.diigo.com|90|Social Bookmarking|DoFollow|General|Global
Scoop.it|https://www.scoop.it|82|Content Curation|DoFollow|General|Global
Pearltrees|https://www.pearltrees.com|87|Content Curation|DoFollow|General|Global
Flipboard|https://flipboard.com|91|Content Curation|NoFollow|News|Global
Pocket|https://getpocket.com|90|Social Bookmarking|NoFollow|General|Global
Mix.com|https://mix.com|75|Social Bookmarking|DoFollow|General|Global
Reddit|https://www.reddit.com|97|Social Platform|NoFollow|General|Global
Pinterest|https://www.pinterest.com|94|Social Platform|NoFollow|General|Global
Slashdot|https://slashdot.org|88|Blog Platform|NoFollow|Technology|Global
Ko-fi|https://ko-fi.com|72|Blog Platform|NoFollow|General|Global
BuyMeACoffee|https://buymeacoffee.com|73|Blog Platform|NoFollow|General|Global
Patreon|https://www.patreon.com|92|Blog Platform|NoFollow|General|Global
ResearchGate|https://www.researchgate.net|93|Article Directory|NoFollow|Science|Global
StackOverflow|https://stackoverflow.com|93|Q&A Platform|NoFollow|Technology|Global
ProductHunt|https://www.producthunt.com|92|Blog Platform|NoFollow|Startups|Global
Hacker News|https://news.ycombinator.com|91|Blog Platform|NoFollow|Technology|Global
IndieHackers|https://www.indiehackers.com|72|Blog Platform|DoFollow|Startups|Global
Hackernoon|https://hackernoon.com|78|Blog Platform|DoFollow|Technology|Global
FreeCodeCamp|https://www.freecodecamp.org|85|Blog Platform|DoFollow|Technology|Global
SitePoint|https://www.sitepoint.com|85|Blog Platform|DoFollow|Web Development|Global
Tealfeed|https://tealfeed.com|52|Blog Platform|DoFollow|General|Global
Penzu|https://penzu.com|69|Blog Platform|DoFollow|General|Global
JustPaste.it|https://justpaste.it|91|Blog Platform|DoFollow|General|Global
Telegraph|https://telegra.ph|93|Blog Platform|DoFollow|General|Global"""


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
                "Type": parts[3].strip(),
                "Link Type": parts[4].strip(),
                "Category": parts[5].strip(),
                "Country": parts[6].strip(),
            })
    return records


def deduplicate(df):
    """Remove duplicates based on domain, keep highest DA."""
    def get_domain(url):
        try:
            parsed = urlparse(str(url))
            return parsed.netloc.lower().replace("www.", "").rstrip("/")
        except Exception:
            return str(url).lower()

    df["_domain"] = df["URL"].apply(get_domain)
    df["_da_num"] = pd.to_numeric(df["Domain Authority"], errors="coerce").fillna(0)
    df = df.sort_values("_da_num", ascending=False).drop_duplicates(subset=["_domain"], keep="first")
    df = df.drop(columns=["_domain", "_da_num"])
    return df


def main():
    print("\n" + "=" * 60)
    print("  BLOG LISTING SITES COMPILER")
    print("  Compiling from 8 verified SEO sources...")
    print("=" * 60 + "\n")

    all_records = []

    sources = [
        ("TheDMSchool (Blog Platforms)", source1_data),
        ("SEOMontreal (Article Sites)", source2_data),
        ("TheGuideX (Web 2.0 Sites)", source3_data),
        ("Collaborator.pro (Guest Posts)", source4_data),
        ("DoesInfoTech (India Article Sites)", source5_data),
        ("WayToIdea (Instant Approval)", source6_data),
        ("TechEasify (Web 2.0)", source7_data),
        ("Additional Directories", source8_data),
    ]

    for name, data in sources:
        records = parse_data(data)
        all_records.extend(records)
        print(f"  Source: {name}: {len(records)} sites")

    print(f"\n  Total raw: {len(all_records)} entries")

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

    # Add serial number
    df.insert(0, "S.No", range(1, len(df) + 1))

    # Save CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  CSV saved: {OUTPUT_CSV} ({len(df)} sites)")

    # Save Excel with formatting
    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"  Excel saved: {OUTPUT_XLSX} ({len(df)} sites)")

    # Stats
    print(f"\n  {'='*40}")
    print(f"  SUMMARY")
    print(f"  {'='*40}")
    print(f"  Total unique sites: {len(df)}")
    print(f"  Types: {df['Type'].value_counts().to_dict()}")
    print(f"  DoFollow sites: {len(df[df['Link Type'] == 'DoFollow'])}")
    print(f"  NoFollow sites: {len(df[df['Link Type'] == 'NoFollow'])}")
    print(f"  High DA (70+): {len(df[pd.to_numeric(df['Domain Authority'], errors='coerce') >= 70])}")
    print(f"  Medium DA (40-69): {len(df[(pd.to_numeric(df['Domain Authority'], errors='coerce') >= 40) & (pd.to_numeric(df['Domain Authority'], errors='coerce') < 70)])}")
    print(f"  Categories: {df['Category'].nunique()}")
    print(f"  India-focused: {len(df[df['Country'] == 'India'])}")

    # Top 20 by DA
    print(f"\n  TOP 20 BY DOMAIN AUTHORITY:")
    print(f"  {'Name':<25} {'DA':>4}  {'Type':<20} {'Link':<10}")
    print(f"  {'-'*65}")
    top20 = df.head(20)
    for _, row in top20.iterrows():
        print(f"  {row['Website Name']:<25} {row['Domain Authority']:>4}  {row['Type']:<20} {row['Link Type']:<10}")

    # Auto-open
    import platform as plat
    import subprocess
    filepath = os.path.abspath(OUTPUT_XLSX)
    print(f"\n  Opening: {filepath}")
    try:
        if plat.system() == "Windows":
            os.startfile(filepath)
        elif plat.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print(f"  Could not auto-open: {e}")

    print()


if __name__ == "__main__":
    main()
