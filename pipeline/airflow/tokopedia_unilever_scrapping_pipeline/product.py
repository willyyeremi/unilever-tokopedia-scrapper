import module
from pathlib import Path


root = Path(__file__).parent.parent

state = 1
url = 'https://www.tokopedia.com/unilever/product'

driver = module.scrapper.driver_maker()
while state == 1:
    link_list, url, state = module.scrapper.product_list_loader(driver, url)
    data_list = module.scrapper.web_data_get(driver, link_list)
    module.scrapper.product_master_input(f'{root}\\credential.csv', data_list)
    module.scrapper.product_input(f'{root}\\credential.csv', data_list)