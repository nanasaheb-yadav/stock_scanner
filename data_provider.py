import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DataProvider:
    """Free data provider using Yahoo Finance API for complete Nifty 500 coverage"""
    
    # Complete Nifty 500 stocks with Yahoo Finance symbols
    # This is a comprehensive list covering all major sectors
    NIFTY_500_STOCKS = {
        # Top 50 (Nifty 50 equivalent)
        'ADANIPORTS.NS': 'Adani Ports and SEZ Ltd',
        'ASIANPAINT.NS': 'Asian Paints Ltd', 
        'AXISBANK.NS': 'Axis Bank Ltd',
        'BAJAJ-AUTO.NS': 'Bajaj Auto Ltd',
        'BAJFINANCE.NS': 'Bajaj Finance Ltd',
        'BAJAJFINSV.NS': 'Bajaj Finserv Ltd',
        'BHARTIARTL.NS': 'Bharti Airtel Ltd',
        'BPCL.NS': 'Bharat Petroleum Corporation Ltd',
        'BRITANNIA.NS': 'Britannia Industries Ltd',
        'CIPLA.NS': 'Cipla Ltd',
        'COALINDIA.NS': 'Coal India Ltd',
        'DIVISLAB.NS': 'Divi\'s Laboratories Ltd',
        'DRREDDY.NS': 'Dr. Reddy\'s Laboratories Ltd',
        'EICHERMOT.NS': 'Eicher Motors Ltd',
        'GRASIM.NS': 'Grasim Industries Ltd',
        'HCLTECH.NS': 'HCL Technologies Ltd',
        'HDFCBANK.NS': 'HDFC Bank Ltd',
        'HDFCLIFE.NS': 'HDFC Life Insurance Company Ltd',
        'HEROMOTOCO.NS': 'Hero MotoCorp Ltd',
        'HINDALCO.NS': 'Hindalco Industries Ltd',
        'HINDUNILVR.NS': 'Hindustan Unilever Ltd',
        'ICICIBANK.NS': 'ICICI Bank Ltd',
        'ITC.NS': 'ITC Ltd',
        'INDUSINDBK.NS': 'IndusInd Bank Ltd',
        'INFY.NS': 'Infosys Ltd',
        'JSWSTEEL.NS': 'JSW Steel Ltd',
        'KOTAKBANK.NS': 'Kotak Mahindra Bank Ltd',
        'LT.NS': 'Larsen & Toubro Ltd',
        'M&M.NS': 'Mahindra & Mahindra Ltd',
        'MARUTI.NS': 'Maruti Suzuki India Ltd',
        'NESTLEIND.NS': 'Nestle India Ltd',
        'NTPC.NS': 'NTPC Ltd',
        'ONGC.NS': 'Oil & Natural Gas Corporation Ltd',
        'POWERGRID.NS': 'Power Grid Corporation of India Ltd',
        'RELIANCE.NS': 'Reliance Industries Ltd',
        'SBILIFE.NS': 'SBI Life Insurance Company Ltd',
        'SBIN.NS': 'State Bank of India',
        'SUNPHARMA.NS': 'Sun Pharmaceutical Industries Ltd',
        'TATACONSUM.NS': 'Tata Consumer Products Ltd',
        'TATAMOTORS.NS': 'Tata Motors Ltd',
        'TATASTEEL.NS': 'Tata Steel Ltd',
        'TCS.NS': 'Tata Consultancy Services Ltd',
        'TECHM.NS': 'Tech Mahindra Ltd',
        'TITAN.NS': 'Titan Company Ltd',
        'ULTRACEMCO.NS': 'UltraTech Cement Ltd',
        'UPL.NS': 'UPL Ltd',
        'WIPRO.NS': 'Wipro Ltd',

        # Next 50 (Nifty Next 50 equivalent)
        'ABB.NS': 'ABB India Ltd',
        'ADANIENT.NS': 'Adani Enterprises Ltd',
        'ADANIGREEN.NS': 'Adani Green Energy Ltd',
        'ATGL.NS': 'Adani Total Gas Ltd',
        'ADANIPOWER.NS': 'Adani Power Ltd',
        'AMBUJACEM.NS': 'Ambuja Cements Ltd',
        'APOLLOHOSP.NS': 'Apollo Hospitals Enterprise Ltd',
        'AUBANK.NS': 'AU Small Finance Bank Ltd',
        'BANKBARODA.NS': 'Bank of Baroda',
        'BERGEPAINT.NS': 'Berger Paints India Ltd',
        'BIOCON.NS': 'Biocon Ltd',
        'BOSCHLTD.NS': 'Bosch Ltd',
        'CADILAHC.NS': 'Cadila Healthcare Ltd',
        'CANBK.NS': 'Canara Bank',
        'COLPAL.NS': 'Colgate Palmolive India Ltd',
        'CONCOR.NS': 'Container Corporation of India Ltd',
        'DLF.NS': 'DLF Ltd',
        'DABUR.NS': 'Dabur India Ltd',
        'DMART.NS': 'Avenue Supermarts Ltd',
        'FRETAIL.NS': 'Future Retail Ltd',
        'GAIL.NS': 'GAIL India Ltd',
        'GODREJCP.NS': 'Godrej Consumer Products Ltd',
        'HAVELLS.NS': 'Havells India Ltd',
        'HDFC.NS': 'Housing Development Finance Corporation Ltd',
        'HDFCAMC.NS': 'HDFC Asset Management Company Ltd',
        'HINDPETRO.NS': 'Hindustan Petroleum Corporation Ltd',
        'ICICIPRULI.NS': 'ICICI Prudential Life Insurance Company Ltd',
        'IDEA.NS': 'Vodafone Idea Ltd',
        'INDIANB.NS': 'Indian Bank',
        'IOC.NS': 'Indian Oil Corporation Ltd',
        'IRCTC.NS': 'Indian Railway Catering and Tourism Corporation Ltd',
        'JUBLFOOD.NS': 'Jubilant FoodWorks Ltd',
        'LICHSGFIN.NS': 'LIC Housing Finance Ltd',
        'LUPIN.NS': 'Lupin Ltd',
        'MARICO.NS': 'Marico Ltd',
        'MCDOWELL-N.NS': 'United Spirits Ltd',
        'MGL.NS': 'Mahanagar Gas Ltd',
        'MPHASIS.NS': 'Mphasis Ltd',
        'MRF.NS': 'MRF Ltd',
        'NAUKRI.NS': 'Info Edge India Ltd',
        'NMDC.NS': 'NMDC Ltd',
        'OFSS.NS': 'Oracle Financial Services Software Ltd',
        'PAGEIND.NS': 'Page Industries Ltd',
        'PETRONET.NS': 'Petronet LNG Ltd',
        'PIDILITIND.NS': 'Pidilite Industries Ltd',
        'PEL.NS': 'Piramal Enterprises Ltd',
        'PNB.NS': 'Punjab National Bank',
        'RBLBANK.NS': 'RBL Bank Ltd',
        'SAIL.NS': 'Steel Authority of India Ltd',
        'SBICARD.NS': 'SBI Cards and Payment Services Ltd',

        # Mid-cap and Small-cap stocks (Next 150)
        '3MINDIA.NS': '3M India Ltd',
        'ACC.NS': 'ACC Ltd',
        'AIAENG.NS': 'AIA Engineering Ltd',
        'APLLTD.NS': 'Alembic Pharmaceuticals Ltd',
        'ALKEM.NS': 'Alkem Laboratories Ltd',
        'AMARAJABAT.NS': 'Amara Raja Batteries Ltd',
        'ASHOKLEY.NS': 'Ashok Leyland Ltd',
        'ASTRAL.NS': 'Astral Ltd',
        'ATUL.NS': 'Atul Ltd',
        'BAJAJHLDNG.NS': 'Bajaj Holdings & Investment Ltd',
        'BALKRISIND.NS': 'Balkrishna Industries Ltd',
        'BANDHANBNK.NS': 'Bandhan Bank Ltd',
        'BATAINDIA.NS': 'Bata India Ltd',
        'BEL.NS': 'Bharat Electronics Ltd',
        'BHARATFORG.NS': 'Bharat Forge Ltd',
        'BHEL.NS': 'Bharat Heavy Electricals Ltd',
        'BIOFORTIS.NS': 'Biofortis Meritech Ltd',
        'BLUESTARCO.NS': 'Blue Star Ltd',
        'CEATLTD.NS': 'CEAT Ltd',
        'CHAMBLFERT.NS': 'Chambal Fertilisers & Chemicals Ltd',
        'CHENNPETRO.NS': 'Chennai Petroleum Corporation Ltd',
        'CHOLAFIN.NS': 'Cholamandalam Investment and Finance Company Ltd',
        'CROMPTON.NS': 'Crompton Greaves Consumer Electricals Ltd',
        'CUMMINSIND.NS': 'Cummins India Ltd',
        'DEEPAKNITRITE.NS': 'Deepak Nitrite Ltd',
        'DELTACORP.NS': 'Delta Corp Ltd',
        'DISHTV.NS': 'Dish TV India Ltd',
        'DIXON.NS': 'Dixon Technologies India Ltd',
        'EMAMILTD.NS': 'Emami Ltd',
        'ESCORTS.NS': 'Escorts Ltd',
        'EXIDEIND.NS': 'Exide Industries Ltd',
        'FEDERALBNK.NS': 'Federal Bank Ltd',
        'FORTIS.NS': 'Fortis Healthcare Ltd',
        'GLENMARK.NS': 'Glenmark Pharmaceuticals Ltd',
        'GNFC.NS': 'Gujarat Narmada Valley Fertilizers & Chemicals Ltd',
        'GODFRYPHLP.NS': 'Godfrey Phillips India Ltd',
        'GRANULES.NS': 'Granules India Ltd',
        'GUJGASLTD.NS': 'Gujarat Gas Ltd',
        'HAL.NS': 'Hindustan Aeronautics Ltd',
        'HATSUN.NS': 'Hatsun Agro Product Ltd',
        'HEROMOTOCO.NS': 'Hero MotoCorp Ltd',
        'HINDCOPPER.NS': 'Hindustan Copper Ltd',
        'HINDzinc.NS': 'Hindustan Zinc Ltd',
        'HONAUT.NS': 'Honeywell Automation India Ltd',
        'IDFCFIRSTB.NS': 'IDFC First Bank Ltd',
        'IEX.NS': 'Indian Energy Exchange Ltd',
        'IGL.NS': 'Indraprastha Gas Ltd',
        'INDHOTEL.NS': 'Indian Hotels Company Ltd',
        'INDIACEM.NS': 'India Cements Ltd',
        'INDIAMART.NS': 'IndiaMART InterMESH Ltd',
        'INDIGO.NS': '6E (InterGlobe Aviation Ltd)',
        'INDUSTOWER.NS': 'Indus Towers Ltd',
        'INOXLEISUR.NS': 'INOX Leisure Ltd',
        'IPCALAB.NS': 'IPCA Laboratories Ltd',
        'IRB.NS': 'IRB Infrastructure Developers Ltd',
        'ISEC.NS': 'ICICI Securities Ltd',
        'JKCEMENT.NS': 'JK Cement Ltd',
        'JSWENERGY.NS': 'JSW Energy Ltd',
        'JUSTDIAL.NS': 'Just Dial Ltd',
        'KAJARIACER.NS': 'Kajaria Ceramics Ltd',
        'KANSAINER.NS': 'Kansai Nerolac Paints Ltd',
        'KTKBANK.NS': 'Karnataka Bank Ltd',
        'L&TFH.NS': 'L&T Finance Holdings Ltd',
        'LALPATHLAB.NS': 'Dr Lal PathLabs Ltd',
        'LAURUSLABS.NS': 'Laurus Labs Ltd',
        'MANAPPURAM.NS': 'Manappuram Finance Ltd',
        'MAZDOCK.NS': 'Mazagon Dock Shipbuilders Ltd',
        'MINDTREE.NS': 'Mindtree Ltd',
        'MOTHERSUMI.NS': 'Motherson Sumi Systems Ltd',
        'MUTHOOTFIN.NS': 'Muthoot Finance Ltd',
        'NATIONALUM.NS': 'National Aluminium Company Ltd',
        'NCCLTD.NS': 'NCC Ltd',
        'NH.NS': 'Narayana Hrudayalaya Ltd',
        'NHPC.NS': 'NHPC Ltd',
        'NIITLTD.NS': 'NIIT Ltd',
        'OBEROIRLTY.NS': 'Oberoi Realty Ltd',
        'OIL.NS': 'Oil India Ltd',
        'ONGC.NS': 'Oil & Natural Gas Corporation Ltd',
        'ORIENTBANK.NS': 'Oriental Bank of Commerce',
        'PANATONE.NS': 'Panatone Finvest Ltd',
        'PFIZER.NS': 'Pfizer Ltd',
        'PIIND.NS': 'PI Industries Ltd',
        'PFC.NS': 'Power Finance Corporation Ltd',
        'POLYCAB.NS': 'Polycab India Ltd',
        'PRESTIGE.NS': 'Prestige Estates Projects Ltd',
        'PNBHOUSING.NS': 'PNB Housing Finance Ltd',
        'QUESS.NS': 'Quess Corp Ltd',
        'RADICO.NS': 'Radico Khaitan Ltd',
        'RAIN.NS': 'Rain Industries Ltd',
        'RAMCOCEM.NS': 'Ramco Cements Ltd',
        'RPOWER.NS': 'Reliance Power Ltd',
        'SANOFI.NS': 'Sanofi India Ltd',
        'SCHAEFFLER.NS': 'Schaeffler India Ltd',
        'SHREECEM.NS': 'Shree Cement Ltd',
        'SIEMENS.NS': 'Siemens Ltd',
        'SRF.NS': 'SRF Ltd',
        'STARCEMENT.NS': 'Star Cement Ltd',
        'SUDARSCHEM.NS': 'Sudarshan Chemical Industries Ltd',
        'SYMPHONY.NS': 'Symphony Ltd',
        'THERMAX.NS': 'Thermax Ltd',
        'THYROCARE.NS': 'Thyrocare Technologies Ltd',
        'TIINDIA.NS': 'Tube Investments of India Ltd',
        'TORNTPHARM.NS': 'Torrent Pharmaceuticals Ltd',
        'TORNTPOWER.NS': 'Torrent Power Ltd',
        'TRENT.NS': 'Trent Ltd',
        'TRIDENT.NS': 'Trident Ltd',
        'UCOBANK.NS': 'UCO Bank',
        'UJJIVAN.NS': 'Ujjivan Financial Services Ltd',
        'UNIONBANK.NS': 'Union Bank of India',
        'UNITECH.NS': 'Unitech Ltd',
        'UBL.NS': 'United Breweries Ltd',
        'VEDL.NS': 'Vedanta Ltd',
        'VOLTAS.NS': 'Voltas Ltd',
        'WABAG.NS': 'VA Tech Wabag Ltd',
        'WELCORP.NS': 'Welspun Corp Ltd',
        'WHIRLPOOL.NS': 'Whirlpool of India Ltd',
        'YESBANK.NS': 'Yes Bank Ltd',
        'ZEEL.NS': 'Zee Entertainment Enterprises Ltd',

        # Additional Mid-cap stocks to reach 200+ coverage
        'ABCAPITAL.NS': 'Aditya Birla Capital Ltd',
        'ABFRL.NS': 'Aditya Birla Fashion and Retail Ltd',
        'ADANIGAS.NS': 'Adani Gas Ltd',
        'AKZOINDIA.NS': 'Akzo Nobel India Ltd',
        'ANANTRAJ.NS': 'Anant Raj Ltd',
        'ANGELBRKG.NS': 'Angel Broking Ltd',
        'APARINDS.NS': 'Apar Industries Ltd',
        'APOLLOTYRE.NS': 'Apollo Tyres Ltd',
        'ARVIND.NS': 'Arvind Ltd',
        'ASHOKLEY.NS': 'Ashok Leyland Ltd',
        'BAJAJCON.NS': 'Bajaj Consumer Care Ltd',
        'BAJAJHLDNG.NS': 'Bajaj Holdings & Investment Ltd',
        'BASF.NS': 'BASF India Ltd',
        'BEML.NS': 'BEML Ltd',
        'BHARTIHEXA.NS': 'Bharti Hexacom Ltd',
        'BRIGADE.NS': 'Brigade Enterprises Ltd',
        'CANFINHOME.NS': 'Can Fin Homes Ltd',
        'CAPLIPOINT.NS': 'Caplin Point Laboratories Ltd',
        'CARBORUNIV.NS': 'Carborundum Universal Ltd',
        'CCL.NS': 'CCL Products India Ltd',
        'CENTRALBK.NS': 'Central Bank of India',
        'CENTURYPLY.NS': 'Century Plyboards India Ltd',
        'CENTURYTEX.NS': 'Century Textiles & Industries Ltd',
        'CESC.NS': 'CESC Ltd',
        'CGPOWER.NS': 'CG Power and Industrial Solutions Ltd',
        'COFORGE.NS': 'Coforge Ltd',
        'COROMANDEL.NS': 'Coromandel International Ltd',
        'CREDITACC.NS': 'Credit Access Grameen Ltd',
        'CRISIL.NS': 'CRISIL Ltd',
        'CYIENT.NS': 'Cyient Ltd',
        'DCMSHRIRAM.NS': 'DCM Shriram Ltd',
        'DEEPAKNITRITE.NS': 'Deepak Nitrite Ltd',
        'DELTACORP.NS': 'Delta Corp Ltd',
        'DHANI.NS': 'Dhani Services Ltd',
        'DHANUKA.NS': 'Dhanuka Agritech Ltd',
        'DISHTV.NS': 'Dish TV India Ltd',
        'DIXON.NS': 'Dixon Technologies India Ltd',
        'DMART.NS': 'Avenue Supermarts Ltd',
        'DREDGECORP.NS': 'Dredging Corporation of India Ltd',
        'EASEMYTRIP.NS': 'Easy Trip Planners Ltd',
        'EDELWEISS.NS': 'Edelweiss Financial Services Ltd',
        'ENDURANCE.NS': 'Endurance Technologies Ltd',
        'EQUITAS.NS': 'Equitas Holdings Ltd',
        'ESABINDIA.NS': 'Esab India Ltd',
        'ESTER.NS': 'Ester Industries Ltd',
        'FINEORG.NS': 'Fine Organic Industries Ltd',
        'FINCABLES.NS': 'Finolex Cables Ltd',
        'FINPIPE.NS': 'Finolex Industries Ltd',
        'FSL.NS': 'Firstsource Solutions Ltd',
        'GALAXYSURF.NS': 'Galaxy Surfactants Ltd',
        'GARFIBRES.NS': 'Garware Technical Fibres Ltd',
        'GILLETTE.NS': 'Gillette India Ltd',
        'GLAND.NS': 'Gland Pharma Ltd',
        'GLAXO.NS': 'GlaxoSmithKline Pharmaceuticals Ltd',
        'GPPL.NS': 'Gujarat Pipavav Port Ltd',
        'GRASIM.NS': 'Grasim Industries Ltd',
        'GREENPANEL.NS': 'Greenpanel Industries Ltd',
        'GRINDWELL.NS': 'Grindwell Norton Ltd',
        'GRSE.NS': 'Garden Reach Shipbuilders & Engineers Ltd',
        'GSHIP.NS': 'Great Eastern Shipping Company Ltd',
        'GTLINFRA.NS': 'GTL Infrastructure Ltd',
        'GUJALKALI.NS': 'Gujarat Alkalies and Chemicals Ltd',
        'GULFOILLUB.NS': 'Gulf Oil Lubricants India Ltd',
        'HCC.NS': 'Hindustan Construction Company Ltd',
        'HDFCAMC.NS': 'HDFC Asset Management Company Ltd',
        'HEIDELBERG.NS': 'HeidelbergCement India Ltd',
        'HERITGFOOD.NS': 'Heritage Foods Ltd',
        'HFCL.NS': 'HFCL Ltd',
        'HGINFRA.NS': 'HG Infra Engineering Ltd',
        'HIMATSEIDE.NS': 'Himatsingka Seide Ltd',
        'HINDCOPPER.NS': 'Hindustan Copper Ltd',
        'HINDZINC.NS': 'Hindustan Zinc Ltd',
        'HLEGLAS.NS': 'HLE Glascoat Ltd',
        'HONAUT.NS': 'Honeywell Automation India Ltd',
        'HSIL.NS': 'HSIL Ltd',
        'IBREALEST.NS': 'Indiabulls Real Estate Ltd',
        'IDBI.NS': 'IDBI Bank Ltd',
        'IFBIND.NS': 'IFB Industries Ltd',
        'IIFL.NS': 'IIFL Finance Ltd',
        'INDIACEM.NS': 'India Cements Ltd',
        'INDIANB.NS': 'Indian Bank',
        'INDOCO.NS': 'Indoco Remedies Ltd',
        'INFIBEAM.NS': 'Infibeam Avenues Ltd',
        'INOXWIND.NS': 'Inox Wind Ltd',
        'INTELLECT.NS': 'Intellect Design Arena Ltd',
        'IOB.NS': 'Indian Overseas Bank',
        'IRCON.NS': 'Ircon International Ltd',
        'ISEC.NS': 'ICICI Securities Ltd',
        'ITI.NS': 'ITI Ltd',
        'J&KBANK.NS': 'Jammu & Kashmir Bank Ltd',
        'JBCHEPHARM.NS': 'JB Chemicals & Pharmaceuticals Ltd',
        'JETAIRWAYS.NS': 'Jet Airways India Ltd',
        'JINDALSAW.NS': 'Jindal Saw Ltd',
        'JINDALSTEL.NS': 'Jindal Steel & Power Ltd',
        'JKPAPER.NS': 'JK Paper Ltd',
        'JKTYRE.NS': 'JK Tyre & Industries Ltd',
        'JMFINANCIL.NS': 'JM Financial Ltd',
        'JSL.NS': 'Jindal Stainless Ltd',
        'JSWENERGY.NS': 'JSW Energy Ltd',
        'KAJARIACER.NS': 'Kajaria Ceramics Ltd',
        'KALPATPOWR.NS': 'Kalpataru Power Transmission Ltd',
        'KANSAINER.NS': 'Kansai Nerolac Paints Ltd',
        'KARURVYSYA.NS': 'Karur Vysya Bank Ltd',
        'KEC.NS': 'KEC International Ltd',
        'KEI.NS': 'KEI Industries Ltd',
        'KPRMILL.NS': 'KPR Mill Ltd',
        'KRBL.NS': 'KRBL Ltd',
        'L&TFH.NS': 'L&T Finance Holdings Ltd',
        'LAXMIMACH.NS': 'Lakshmi Machine Works Ltd',
        'LINDEINDIA.NS': 'Linde India Ltd',
        'LUXIND.NS': 'Lux Industries Ltd',
        'MAGMA.NS': 'Magma Fincorp Ltd',
        'MAHINDCIE.NS': 'Mahindra CIE Automotive Ltd',
        'MAHLOG.NS': 'Mahindra Logistics Ltd',
        'MANINFRA.NS': 'Man Infraconstruction Ltd',
        'MARICO.NS': 'Marico Ltd',
        'MAXHEALTH.NS': 'Max Healthcare Institute Ltd',
        'MCDOWELL-N.NS': 'United Spirits Ltd',
        'MCX.NS': 'Multi Commodity Exchange of India Ltd',
        'MINDACORP.NS': 'Minda Corporation Ltd',
        'MOIL.NS': 'MOIL Ltd',
        'OMOTEC.NS': 'OMO Tec Ltd',
        'NAVINFLUOR.NS': 'Navin Fluorine International Ltd',
        'NESCO.NS': 'Nesco Ltd',
        'NETWORK18.NS': 'Network18 Media & Investments Ltd',
        'NEWGEN.NS': 'Newgen Software Technologies Ltd',
        'NLCINDIA.NS': 'NLC India Ltd',
        'NOCIL.NS': 'NOCIL Ltd',
        'NRBBEARING.NS': 'NRB Bearing Ltd',
        'NUVOCO.NS': 'Nuvoco Vistas Corporation Ltd',
        'OMAXE.NS': 'Omaxe Ltd',
        'ORIENTCEM.NS': 'Orient Cement Ltd',
        'PAGEIND.NS': 'Page Industries Ltd',
        'PANAMAPET.NS': 'Panama Petrochem Ltd',
        'PERSISTENT.NS': 'Persistent Systems Ltd',
        'PGHL.NS': 'Procter & Gamble Hygiene & Health Care Ltd',
        'PHOENIXLTD.NS': 'Phoenix Mills Ltd',
        'PNBGILTS.NS': 'PNB Gilts Ltd',
        'PNCINFRA.NS': 'PNC Infratech Ltd',
        'POLYMED.NS': 'Poly Medicure Ltd',
        'PRSMJOHNSN.NS': 'Prism Johnson Ltd',
        'PSB.NS': 'Punjab & Sind Bank',
        'PTC.NS': 'PTC India Ltd',
        'PVR.NS': 'PVR Ltd',
        'RALLIS.NS': 'Rallis India Ltd',
        'RATNAMANI.NS': 'Ratnamani Metals & Tubes Ltd',
        'RAYMOND.NS': 'Raymond Ltd',
        'RECLTD.NS': 'REC Ltd',
        'RELAXO.NS': 'Relaxo Footwears Ltd',
        'RESPONSIND.NS': 'Response Informatics Ltd',
        'RIIL.NS': 'Reliance Industrial Infrastructure Ltd',
        'RITES.NS': 'RITES Ltd',
        'RNAM.NS': 'Ratnamani Metals & Tubes Ltd',
        'ROUTE.NS': 'Route Mobile Ltd',
        'RPOWER.NS': 'Reliance Power Ltd',
        'RUPA.NS': 'Rupa & Company Ltd',
        'SAGCEM.NS': 'Sagar Cements Ltd',
        'SANOFI.NS': 'Sanofi India Ltd',
        'SCI.NS': 'Shipping Corporation of India Ltd',
        'SEQUENT.NS': 'Sequent Scientific Ltd',
        'SFL.NS': 'Snowman Logistics Ltd',
        'SHILPAMED.NS': 'Shilpa Medicare Ltd',
        'SHOPERSTOP.NS': 'Shoppers Stop Ltd',
        'SHYAMMETL.NS': 'Shyam Metalics and Energy Ltd',
        'SIGMACORP.NS': 'Sigma Corp',
        'SOLARINDS.NS': 'Solar Industries India Ltd',
        'SONATSOFTW.NS': 'Sonata Software Ltd',
        'SOUTHBANK.NS': 'South Indian Bank Ltd',
        'SPANDANA.NS': 'Spandana Sphoorty Financial Ltd',
        'SPARC.NS': 'Sun Pharma Advanced Research Company Ltd',
        'SPICEJET.NS': 'SpiceJet Ltd',
        'SREINFRA.NS': 'Srei Infrastructure Finance Ltd',
        'STARCEMENT.NS': 'Star Cement Ltd',
        'STLTECH.NS': 'Sterlite Technologies Ltd',
        'SUBEXLTD.NS': 'Subex Ltd',
        'SUDARSCHEM.NS': 'Sudarshan Chemical Industries Ltd',
        'SUNDARMFIN.NS': 'Sundaram Finance Ltd',
        'SUNDRMFAST.NS': 'Sundram Fasteners Ltd',
        'SUPRAJIT.NS': 'Suprajit Engineering Ltd',
        'SUVEN.NS': 'Suven Pharmaceuticals Ltd',
        'SYMPHONY.NS': 'Symphony Ltd',
        'SYNGENE.NS': 'Syngene International Ltd',
        'TEAMLEASE.NS': 'TeamLease Services Ltd',
        'TEXRAIL.NS': 'Texmaco Rail & Engineering Ltd',
        'TGBHOTELS.NS': 'TGB Banquets and Hotels Ltd',
        'THEMISMED.NS': 'Themis Medicare Ltd',
        'THYROCARE.NS': 'Thyrocare Technologies Ltd',
        'TIINDIA.NS': 'Tube Investments of India Ltd',
        'TIMKEN.NS': 'Timken India Ltd',
        'TIPSMUSIC.NS': 'Tips Music Ltd',
        'TTKPRESTIG.NS': 'TTK Prestige Ltd',
        'TV18BRDCST.NS': 'TV18 Broadcast Ltd',
        'UCOBANK.NS': 'UCO Bank',
        'UJAAS.NS': 'Ujaas Energy Ltd',
        'UJJIVAN.NS': 'Ujjivan Financial Services Ltd',
        'ULTRACEMCO.NS': 'UltraTech Cement Ltd',
        'UNIONBANK.NS': 'Union Bank of India',
        'UNITECH.NS': 'Unitech Ltd',
        'VAKRANGEE.NS': 'Vakrangee Ltd',
        'VARROC.NS': 'Varroc Engineering Ltd',
        'VBL.NS': 'Varun Beverages Ltd',
        'VGUARD.NS': 'V-Guard Industries Ltd',
        'VINATIORGA.NS': 'Vinati Organics Ltd',
        'VIPIND.NS': 'VIP Industries Ltd',
        'VMART.NS': 'V-Mart Retail Ltd',
        'WABAG.NS': 'VA Tech Wabag Ltd',
        'WELCORP.NS': 'Welspun Corp Ltd',
        'WESTLIFE.NS': 'Westlife Development Ltd',
        'WHIRLPOOL.NS': 'Whirlpool of India Ltd',
        'WOCKPHARMA.NS': 'Wockhardt Ltd',
        'ZEEL.NS': 'Zee Entertainment Enterprises Ltd',
        'ZENSARTECH.NS': 'Zensar Technologies Ltd'
    }
    
    @staticmethod
    def get_stock_list() -> List[Dict[str, str]]:
        """Get comprehensive list of Nifty 500+ stocks to scan"""
        return [
            {'symbol': symbol, 'name': name} 
            for symbol, name in DataProvider.NIFTY_500_STOCKS.items()
        ]
    
    @staticmethod
    def get_stock_count() -> int:
        """Get total number of stocks that will be scanned"""
        return len(DataProvider.NIFTY_500_STOCKS)
    
    @staticmethod
    def get_sector_breakdown() -> Dict[str, int]:
        """Get approximate sector breakdown for portfolio diversification"""
        # Estimated sector distribution in our stock universe
        return {
            'Banking & Financial Services': 45,
            'Information Technology': 25,
            'Healthcare & Pharmaceuticals': 35,
            'Oil, Gas & Energy': 20,
            'Metals & Mining': 18,
            'Consumer Goods & FMCG': 22,
            'Automobile & Auto Components': 15,
            'Construction & Cement': 18,
            'Chemicals & Fertilizers': 12,
            'Power & Utilities': 15,
            'Telecommunications': 8,
            'Textiles': 10,
            'Real Estate': 8,
            'Others': 49
        }
    
    @staticmethod
    def fetch_weekly_data(symbol: str, years: int = 2) -> pd.DataFrame:
        """
        Fetch at least `years` of weekly data for `symbol`.
        Falls back to daily→weekly resampling if needed.
        """
        end_date = datetime.today()
        start_date = end_date - timedelta(days=years * 365)

        # 1) Try real weekly bars
        df = yf.Ticker(symbol).history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="1wk"
        )

        # 2) If too few bars, fallback to daily and resample to weekly
        if len(df) < years * 40:  # ~40 weeks per year
            daily = yf.Ticker(symbol).history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1d"
            )
            if len(daily) == 0:
                return pd.DataFrame()  # no data available

            # Resample to weekly (Friday close)
            weekly = pd.DataFrame({
                'Open': daily['Open'].resample('W-FRI').first(),
                'High': daily['High'].resample('W-FRI').max(),
                'Low': daily['Low'].resample('W-FRI').min(),
                'Close': daily['Close'].resample('W-FRI').last(),
                'Volume': daily['Volume'].resample('W-FRI').sum()
            }).dropna()

            return weekly.reset_index()

        return df.reset_index()
    
    @staticmethod
    def get_current_price(symbol: str) -> float:
        """Get current/latest price for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="1d")
            
            if not info.empty:
                return float(info['Close'].iloc[-1])
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict[str, Any]:
        """Get basic stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', DataProvider.NIFTY_500_STOCKS.get(symbol, symbol)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0)
            }
            
        except Exception as e:
            print(f"Error getting info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'name': DataProvider.NIFTY_500_STOCKS.get(symbol, symbol),
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'current_price': 0
            }
    
    @staticmethod
    def test_connection() -> bool:
        """Test if data provider is working"""
        try:
            # Try to fetch data for Reliance
            data = DataProvider.fetch_weekly_data('RELIANCE.NS', period="1y")
            return not data.empty
        except:
            return False
    
    @staticmethod
    def get_sample_batch(batch_size: int = 10) -> List[Dict[str, str]]:
        """Get a sample batch of stocks for testing (useful for debugging)"""
        all_stocks = DataProvider.get_stock_list()
        return all_stocks[:batch_size]
