import scrapy
from scrapy.shell import inspect_response
from scrapy.crawler import CrawlerProcess
from scrapy_splash import SplashRequest
from parsel import Selector
import time
from db_controller import DBController
from file_controller import FileController
import random

#Unfortunatelly, decrees don't follow a very consistent pattern along the years and you might have to change the xPath depending on the texts you're trying to crawl.

class DecretoSpider(scrapy.Spider):
    DOWNLOADER_MIDDLEWARES = {
        'scrapy_splash.SplashCookiesMiddleware': 723,
        'scrapy_splash.SplashMiddleware': 725,
        'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    }
    SPLASH_URL = 'http://localhost:8050'
    DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
    HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

    name            = 'decretos_spider'
    start_urls      = ['http://www.planalto.gov.br/CCIVIL_03/decreto/Quadros/2000.htm'] #URL com a lista de decretos
    year = 2000

    def parse(self, response):
        DBController.start_bd()
        links_decretos = response.xpath("/html/body/div//table//tr/td//a/@href").extract()   #padrão do quadro de 2001 e 2000
        #links_decretos = response.xpath("/html/body/table//tr/td[1]//a/@href").extract()   #padrão do quadro de 2003
        #links_decretos = response.xpath("/html/body/div/table//tr/td//a/@href").extract()  #padrão genérico
        print("Encontrados ", len(links_decretos), " decretos em ", self.start_urls, ".")
        already_saved = DBController.get_already_saved()

        try_list = []   # If some pages get stucked in the first trial, include them in the try_list

        counter = 0
        for page in links_decretos:
            if(counter < 50): #and response.urljoin(page) in try_list):                   #I stronggly recommend downloading at most 100 decrees each time, otherwise the website starts denying the connection.
                if page is not None and response.urljoin(page) not in already_saved:
                    request = response.follow(page, self.parse_decreto)
                    request.meta['link_id'] = response.urljoin(page)
                    yield request

                    time.sleep(random.uniform(1.0, 2.5))
                    if counter%25 == 0 and counter!=0:
                        time.sleep(random.uniform(30.0, 90.0))
            counter = counter+1
        #DBController.conn.close()      know when all parse've finished to close DB connection

    def parse_decreto(self, response):
        link_id = response.meta['link_id']

        valid_text = response.xpath("/html/body//text()[not(ancestor::table)][not(ancestor::a)][not(ancestor::header)][not(ancestor::nav)] | (/html/body//table)[position()>2]//text() | (/html/body//a)[position()>1]//text()").extract()
        for i in range(len(valid_text)):
            sel = Selector(text=valid_text[i])
            valid_text[i] = valid_text[i].replace("\xa0", ' ')
            aux_valid_text = sel.xpath('normalize-space(//text())').extract()
            valid_text[i] = aux_valid_text[0]
            if i != 0 and valid_text[i] != '':
                valid_text[0]+=" "
                valid_text[0]+=valid_text[i]
        if len(valid_text) > 0:
            valid_text = valid_text[0]
        else:
            valid_text = ''

        valid_text = " ".join(valid_text.split())        #remove repeated white spaces
        valid_text = valid_text.split("Este texto não substitui o publicado")[0]    #remove anexos
        if valid_text.find("Vigência ") == 0:
            valid_text = valid_text.replace("Vigência ", "", 1)

        if valid_text.find("O PRESIDENTE DA REPÚBLICA") != -1:
            valid_text = " ".join(["O PRESIDENTE DA REPÚBLICA", valid_text.split("O PRESIDENTE DA REPÚBLICA", 1)[1]])
        if valid_text.find("O VICE-PRESIDENTE DA REPÚBLICA") != -1:
            valid_text = " ".join(["O VICE-PRESIDENTE DA REPÚBLICA", valid_text.split("O VICE-PRESIDENTE DA REPÚBLICA", 1)[1]])

        links = response.xpath("/html/body//a/@href").extract()
        links = [response.urljoin(link) for link in links]
        if(len(links) > 0):
            del links[0]
            if(len(links)>=1):
                links = ", ".join(links)
            else:
                links = None
        yield{"Links do decreto: ": links}

        table_data_link = response.xpath("(/html/body//a/@href)[1]").extract()
        if(len(table_data_link) != 0):
            #página obtida normalmente
            table_data_link = table_data_link[0]
            table_data_link = table_data_link.replace("%20", " ")
            yield {'Link da tabela: ': table_data_link}

            request = SplashRequest(url=table_data_link, callback=self.parse_data_table, endpoint='render.html', args={'wait': 2.5}, dont_filter=True)
            request.meta['link_id'], request.meta['links'] = link_id, links
            request.meta['full_html'], request.meta['valid_text'] = response.body, valid_text

            yield request
        else:
            #tentativa de reconexão
            n_try = 3      #Define quantas vezes tentar acessar a página recursivamente. Se 1, não tenta reacessar.
            try:
                if(response.meta['retry_times'] < n_try):
                    yield{'ERRO ': "Tentando novamente automaticamente."}
                    time.sleep(1)
                    request = scrapy.Request(response.url, callback=self.parse_decreto, dont_filter=True)
                    request.meta['link_id'] = response.meta['link_id']
                    request.meta['retry_times'] = response.meta['retry_times'] + 1
                    yield request
                else:
                    yield {'ERRO': "Link não obtido. Repita a operação manualmente."}
                    DBController.save_error(response.meta['link_id']) #salvar o id do decreto em uma tabela de decretos com erro de obtenção.
            except KeyError:
                if(n_try != 1):
                    yield{'ERRO ': "Tentando novamente automaticamente."}
                    time.sleep(1)
                    request = scrapy.Request(response.url, callback=self.parse_decreto, dont_filter=True)
                    request.meta['link_id'] = response.meta['link_id']
                    request.meta['retry_times'] = 2
                    yield request
                else:
                    yield {'ERRO': "Link não obtido. Repita a operação manualmente."}
                    DBController.save_error(response.meta['link_id']) #salvar o id do decreto em uma tabela de decretos com erro de obtenção.


    def parse_data_table(self, response):
        full_data_table_html = response.body
        information_name = response.xpath("/html/body/form/table/tbody//tr/th//text()").extract()
        information = []
        counter = 0
        for td in response.xpath("/html/body/form/table//tr/td").extract():
            sel = Selector(text=td)
            information.append(sel.xpath('//text()').extract())
            information[len(information)-1] = " ".join(information[len(information)-1])
            if(counter == 7):
                alteracao_full = td

            counter=counter+1

        if len(information) != 0:
            data_assinatura_ato = response.xpath("(/html//input[@type='hidden' and @name='DAT_ASSINATURA_ATO']/@value)").extract()[0]
            num_ato = response.xpath("(/html//input[@type='hidden' and @name='NUM_ATO']/@value)").extract()[0]
            cod_ident_ato = response.xpath("(/html//input[@type='hidden' and @name='COD_IDENT_ATO']/@value)").extract()[0]
            alteracao = information[7]

            classificacao_de_direito = response.xpath("(/html//input[@type='hidden' and @name='DSC_CATALOGO']/@value)").extract()
            classificacao_de_direito = [item.strip().rstrip('.').strip() for classificacao in classificacao_de_direito for item in classificacao.split(' , ')]
            
            information[5] = response.meta['link_id']
            assunto = [item.strip() for item in information[11].replace('.', '').split(", ")]
            DBController.save_data(response.meta['valid_text'], response.meta['links'], information[0], information[1], information[2], information[3], information[4], information[5], information[6], alteracao, alteracao_full, information[8], information[9], information[10], assunto, classificacao_de_direito, information[13], data_assinatura_ato, num_ato, cod_ident_ato)
            FileController.save_decreto_file(DecretoSpider.year, num_ato, response.meta['full_html'])
            FileController.save_data_file(DecretoSpider.year, num_ato, full_data_table_html)
        else:
            yield{'ERRO ': "Tabela de dados não obtida. Repita a operação."}
            DBController.save_error(response.meta['link_id']) #salvar o id do decreto em uma tabela de decretos com erro de obtenção.

        for i in range(len(information_name)):
            yield{information_name[i]: information[i]}
