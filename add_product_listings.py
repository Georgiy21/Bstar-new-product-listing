import csv
import pandas as pd
import re
from datetime import datetime
from datetimerange import DateTimeRange
from datetime import timedelta
# * Use OOP for the next vendors

#! Structure:
# 1) Extract all the necessary information from the price list
# 2) Preprocess the information to match the template_column_name
# 3) Write to a file all the information

columns = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker', 'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping', 'Variant Taxable', 'Variant Barcode', 'Image Src', 'Image Position', 'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description',
           'Google Shopping / Google Product Category', 'Google Shopping / Gender', 'Google Shopping / Age Group', 'Google Shopping / MPN', 'Google Shopping / AdWords Grouping', 'Google Shopping / AdWords Labels', 'Google Shopping / Condition', 'Google Shopping / Custom Product', 'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1', 'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3', 'Google Shopping / Custom Label 4', 'Variant Image', 'Variant Weight Unit', 'Variant Tax Code', 'Cost per items']

info_fields = ['Model #', 'Image 1', 'Image 2', 'Image 3', 'Image 4', 'Image 5', 'Image 6', 'Image 7', 'Image 8', 'Image 9', 'Image 10', 'Image 11',
               'Image 12', 'Product Name', 'Features', 'Brand', 'Total Weight', 'Delivered Cost CA', 'Depth', 'Width', 'Height', 'Cost', 'UPC Code', 'Color', 'Category #1', 'Category #2']
           
vendor = 'Pending - Bestar'
published = 'FALSE'
variant_inventory_tracker = 'shopify'
variant_inventory_policy = 'deny'
variant_fulfillment_service = 'manual'
variant_taxable = 'TRUE'
variant_requires_shipping = 'TRUE'
gift_card = 'FALSE'
weight_unit = 'lb'

# Get 1 WEEK daterange from today's date 
datemask = '%m-%d-%Y'

future = datetime.today() + timedelta(days=7)
fday = datetime.strftime(future, datemask)

tday = datetime.today().strftime(datemask)
today = datetime.strptime(tday, datemask)

time_range = DateTimeRange(tday, fday)

                       
#! Change the source file to have only new products
# Remove first line and preprocess second line to be the header for key/value pairs
# Return a list of new product SKUs with info: ['Model # ', 'Images[1-12]', 'Product Name', 'Features', 'Brand', 'Delivered Cost CA', 'Cost', 'Total Weight', '1', 'UPC Code']
def preprocess_file(file_p, file_m):

    p_dict = []
    new_skus = []
    price_list = []

    new_products = pd.read_csv(file_m)

    # Append all SKUs from 'Price List-Bestar-Matt' to new_skus list
    for row in new_products.to_dict('records'):
        for k, v in row.items():
            if k == 'Model # ':
                new_skus.append(v)

    price_file = pd.read_csv(file_p, header=[1])

    # Rename column names
    price_file.rename(columns={
                      'Model # ': 'Model #', 'Total' + '\n' + 'Weight': 'Total Weight'}, inplace=True)
    for i in range(1, 13):
        price_file.rename(columns={str(i): 'Image ' + str(i)}, inplace=True)

    # Find SKUs from the price list that are new and append it to p_dict
    for row in price_file.to_dict('records'):
        for k, v in row.items():
            if k == 'Model #' and v in new_skus:
                p_dict.append(row)

    # Create price_list of new skus with info as key/value pairs
    for d in p_dict:
        li = []
        for k, v in d.items():
            if k in info_fields:
                li.append((k, v))
        price_list.append(dict(li))

    return price_list

# Get Product Name, replace space and --- with a single - to get handle
# For variants of product, have one handles for each variant
# Get title of the product. If variants, get modified title
def get_title_handle(pl):

    count = 0
    handle = ''
    title = ''
    mod_title = ''

    for product in pl:
        for k, v in product.items():
            if k == 'Product Name':
                title = v.replace('Bestar' , '').strip()
                if handle == '':
                    handle = title.lower().replace(' ', '-').replace('---', '-')
                else:
                    continue


    if len(pl) > 1:
        mod_title = title.rsplit('-', 1)[0].strip()
        title = mod_title + ' - Available in ' + str(len(pl)) + ' Colours'
        handle = mod_title.lower().replace(' ', '-')

        
    return title, handle

# Generate Alt Img Text
def get_img_alt_text(items):
    
    img_alt_text = []

    for product in items:
        img_alt_text.append(product['Product Name'].replace('Bestar', 'Modubox').strip())
    
   
    return img_alt_text

# Split and preprocess 'Features' text into tokens
# [-] splits two tokens written together
# [-] merges incomplete sentces into one
def get_text(product):

    text = ''
    complete_sentences = []
    for k, v in product.items():
        if k == 'Features':
            text = v

    x = re.split(r'(([A-Za-z])[.!?)])', text)
    
    for sent in range(len(x)):
        try:
            if len(x[sent]) > 2:
                if len(x[sent + 1]) == 2:
                    sentence = x[sent].lstrip('.').strip()
                    if ')' in  x[sent + 1]:
                        sentence += x[sent + 1] + '.'
                    else:
                        sentence += x[sent + 1]
            else:
                continue
            complete_sentences.append(sentence)
        except IndexError:
            complete_sentences.append(x[sent])

    # print('COMPLETE SENTENCES: ' , complete_sentences)
    return complete_sentences

# Categorize sentences into desription, specifications, dimensions
def categorize_text(text):
    description = []
    specifications = []
    dimensions = []

    # classify sentences into dimensions, specifications, and description
    spec_sent = ''
    dim_sent = ''
    try:
        for sent in text:
            splitted = sent.split()
            first = splitted[0]
            second = splitted[1]

            if first.isupper():
                spec_sent += sent + ' '
                specifications.append(sent + ' ')
            else:
                if spec_sent != '':
                    specifications.append(sent + ' ')
                else:
                    description.append(sent + ' ')
    except IndexError:
        pass
    
    warranty = ''
    # Add sentences from specifications to desciption
    try:
        for i in specifications:
            if warranty != '':
                description.append(i)           
            else:
                if "limited warranty." in i:
                    warranty = i
    except IndexError:
        pass

    # Add dimensions sentences and delete them from specifications
    for s in specifications:
        index = specifications.index(s)
        q = s.count('”') 
        q1 = s.count('"') 
        q2 = s.count('“')
        
        if q > 2 or q1 > 2 or q2 > 2:
            if '(2 people).' in s or ').' in s:
                if '"' in s or '”' in s:
                    pass
                else:
                    dim = s.split(').')[1].strip()
                    temp = s.split(').')[0].strip()
                    spec = temp + ').'
                    dimensions.append(dim)
                    specifications.remove(s)
                    specifications.insert(index, spec)
            else:
                dimensions.append(s)
    
    # Remove dimensions sentences from descitpion
    for s in description:
        q = s.count('”') 
        q1 = s.count('"') 
        q2 = s.count('“')
        
        if q > 2 or q1 > 2 or q2 > 2:
            dimensions.append(s)
            description.remove(s)

    specifications = [x for x in specifications if x not in description and x not in dimensions]
    description = [x for x in description if x not in specifications and x not in dimensions]
    
    # Strip white spaces between '.' and '"' in dimensions
    for d in dimensions:
        index = dimensions.index(d)
        dim = ''
        if ', commercial' in d:
            dim = d.split(', commercial')[0].strip().replace(" ","").replace('x', ' x ')
            dimensions.remove(d)
        elif 'mattresses' in d or 'mattress' in d:
            pass
        elif 'Dimensions:' in d:
            dim = d.replace('Dimensions: ', '').replace(" ","").replace('x', ' x ').replace(':',': ')
            dimensions.remove(d)
        else:     
            dim = d.replace(" ","").replace('x', ' x ').replace(':',': ')
            dimensions.remove(d)
        dimensions.insert(index, dim)

    # print('Specifications: ' , specifications)
    # print("\nDescription: " , description)
    # print('\nDimensions: ' , dimensions)

    return description, specifications, dimensions

# Produce text in HTML format
def get_body_html(pl, p_type):

    body = ''

    for product in pl:
        text = get_text(product)
        break

    description, specifications, dimensions = categorize_text(text)

    # Append sentences in DESCRIPTION list to body IF EXIST
    if description:
        desc = ''
        for row in description:
            desc += row

        body += '<h4>Description</h4>\n' + '<p>Items Included</p>\n<ul>\n'

        if dimensions:
            item_included = ''
            for x in dimensions:
                if ':' in x and ('Overall dimensions:' not in x or 'Overalldimensions:' not in x or 'Interiordimensionsofthedrawersare' not in x):
                    item_included = x.split(':')[0].strip()
                    body += '<li>' + item_included + '</li>\n'
            if item_included == '':
                body += '<li>' + p_type + '</li>\n'
        else:
            body += '<li>' + p_type + '</li>\n'
        body += '</ul>\n' + '<meta charset="utf-8">\n'
        body += '<p><span>' + desc + '</span></p>\n'
        
    else:
        pass
    
    # Get dimensions from columns 'Width' 'Depth' 'Height' 
    # Do not include if v == 'See features'
    dim_sent = ''
    for product in pl:
        if dim_sent == '':
            for k,v in product.items():
                if k == 'Width' and v != 'See features':
                    dim_sent += v + '"W'
                elif k == 'Depth' and v != 'See features':
                    dim_sent += ' x ' + v + '"D'
                elif k == 'Height' and v != 'See features':
                    dim_sent += ' x ' + v + '"H'
        else:
            continue
 

    # Append sentences in DIMENSIONS list to body IF EXIST
    if dimensions or dim_sent:
        body += '<h4>Dimensions</h4>\n'   
        for row in dimensions: 
            body += '<p>' + row + ' ' + '</p>\n'

        if dimensions and 'Overalldimensions:' in body:
            pass
        elif not dimensions or 'Interiordimensionsofthedrawersare' in body or 'Interiordimensionsofdrawerare' in body:
            body += '<p>' + 'Overall Dimensions: ' + dim_sent + '</p>\n'

    # Append sentences in SPECIFICATIONS list to body IF EXIST
    if specifications:
        body += '<h4>Specifications</h4>\n' + '<ul>\n'
        sent = ''
        list1 = []
        for row in specifications:
            words = row.split()
            first = words[0]

            if first.isupper():
                if sent != '':
                    body += '<li>' + sent + '</li>\n'
                    sent = ''
                    sent += row
                else:
                    sent += row
            elif first == 'Assembly':
                body += '<li>' + row + '</li>\n'
            else:
                sent += row

        body += '<li>' + sent + '</li>\n' + '</ul>'
    else:
        pass

    return body

# Get tags of each product and append it to listw
def gen_tags(pl):

    product_tags = ['Bestar', 'Brand_Modubox', 'Made In_Canada', 'Style_Contemporary']

    for product in pl:
        for k, v in product.items():
            if k == 'Color':
                if '&' in v:
                    tag1 = 'Colour_' + v.split('&')[0].strip()
                    tag2 = 'Colour_' + v.split('&')[1].strip()
                    if tag1 not in product_tags:
                        product_tags.append(tag1)
                    if tag2 not in product_tags:
                        product_tags.append(tag2)
                    else:
                        pass
                else:
                    tag1 = 'Colour_' + v.strip()
                    product_tags.append(tag1)
            elif k == 'Category #1':
                # print("'",v,"'")
                # if v in (None, ""):
                #     continue
                if v == 'Desks' and 'Type_Desk' not in product_tags:
                    product_tags.append('Type_Desk')
                # elif 'Office' in v and 'Room_Home Office' not in product_tags:
                #     product_tags.append('Room_Home Office')
                
            elif k == 'Category #2':
                # if not v:
                #     continue
                if 'Desk' in v and 'Room_Home Office' not in product_tags:
                    product_tags.append('Room_Home Office')
                elif 'Office ' in v and 'Type_Desk' not in product_tags:
                    product_tags.append('Type_Desk')
            else:
                continue

    return product_tags

# Get a list of images of the product
def get_image(pl):

    img_lists = []
 
    for product in pl:
        images = []
        for k,v in product.items():
            if 'Image' in k:
                if str(v) == 'nan':
                    continue
                else:
                    images.append(v)
        img_lists.append(images)

    return img_lists

# Get the type for the product
def get_type(pl):

    type_name = ''

    for product in pl:
        for k, v in product.items():
            if k == 'Category #2':
                type_name = v
        break

    return type_name

# Get the Total Weight of each product and append it to list
# ? round up decimal number
def get_weight(pl):
    
    weights = []

    for product in pl:
        total_weight = ''
        for k, v in product.items():
            if k == 'Total Weight':
                total_weight = int(v) * 453.592
        weights.append(str(total_weight))
    return weights

# Get the UPC code of every product varient and append to list.
# Remove trailing 0 and put it at the front
def get_upc(pl):

    barcodes = []
    barcode = ''
    for product in pl:
        for k, v in product.items():
            if k == 'UPC Code':
                barcode = '\'0' + str(v).strip('.0')
                barcodes.append(barcode)
    
    return barcodes

# Get the option name and value and put it into a dict
# Options [Color, Size, Title]
def get_option_name_value(pl):

    product_list = []

    option = False

    for product in pl:
        option_dict = dict()
        for k, v in product.items():
            # change this part
            if k == 'Color':
                option_dict['Colour'] = v
                option = True
            else:
                continue
        product_list.append(option_dict)

    if option == False:
        option_dict['Title'] = 'Default Title'
        product_list.append(option_dict)

    # print(product_list)

    return product_list

def get_seo_title(title):

    seo_title = ''

    if "-" in title:
        seo_title = 'Modubox ' + title.rsplit(' - ')[0].strip()

    return seo_title

# Get the SKU of each product and append to list
def get_sku(pl):

    sku = ''
    skus = []
    for product in pl:
        for k, v in product.items():
            if k == 'Model #':
                sku = v
        skus.append(sku)
    
    return skus

def get_cost_per_item(pl):

    costs = []

    for product in pl:
        for k,v in product.items():
            if k == 'Delivered Cost CA':
                price = v.split('$')[1].strip().replace(',','')
                costs.append(price)
 
    return costs

# Get Price and Compare At Price from 'Price List-Bestar-Matt.csv' file
def get_price(pl, filename_matt):

    price_list = pd.read_csv(filename_matt)
    temp = []
    products = []
    price = []

    for line in price_list.to_dict('records'):
        temp.append([line['Model # '], line['Price'], line['Compare At Price']])

    for product in pl:
        for k,v in product.items():
            if k == 'Model #':
                products.append(v)

    
    for p_list in temp:
        for pr in products:
            if pr == p_list[0]:
                price.append([p_list[1], p_list[2]])

    return price

# get quantity from the Bestar inventory sheet that's sent every day
def get_quantity(pl, inventory_filename):

    stock = []  
    skus = []
    existing_sku = []

    with open(inventory_filename, 'r', encoding='utf8') as inventory_file:
        inventory = csv.DictReader(inventory_file)
        inv_qty = []
        
        for line in inventory:
            if line['NEXT DATE'] != '':
                if line['NEXT DATE'] in time_range:
                    line['QTY'] = line['NEXT QTY']
            inv_qty.append([line['\ufeffITEM'], line['QTY']])
            existing_sku.append(line['\ufeffITEM'])

    for product in pl:
        for k,v in product.items():
            if k == 'Model #':
                skus.append(v)

    for sku in skus:
        if sku in existing_sku:
            for pair in inv_qty:
                if sku in pair[0]:
                    stock.append(pair[1])
        else:
            stock.append('-50')

    for qty in stock:
        index = stock.index(qty)
        new_q = 0
        if qty == '-50':
            continue
        elif int(float(qty)) < 5:
            stock.remove(qty)
            stock.insert(index, new_q)
    # print(stock)

    return stock

# Generate a product line to be written to the output.csv file
def produce_template_line(seo_title, handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, quantity, cost_per_item, price, main_img, alt_text, img, obj, obj_num):

    template_header = {'Handle': '', 'Title': '', 'Body (HTML)': '',
                       'Vendor': '', 'Type': '', 'Tags': '', 'Published': '', 'Option1 Name': '',
                       'Option1 Value': '', 'Option2 Name': '', 'Option2 Value': '', 'Option3 Name': '',
                       'Option3 Value': '', 'Variant SKU': '', 'Variant Grams': '', 'Variant Inventory Tracker': '',
                       'Variant Inventory Qty': '', 'Variant Inventory Policy': '', 'Variant Fulfillment Service': '',
                       'Variant Price': '', 'Variant Compare At Price': '', 'Variant Requires Shipping': '',
                       'Variant Taxable': '', 'Variant Barcode': '', 'Image Src': '', 'Image Position': '',
                       'Image Alt Text': '', 'Gift Card': '', 'SEO Title': '', 'SEO Description': '',
                       'Google Shopping / Google Product Category': '', 'Google Shopping / Gender': '',
                       'Google Shopping / Age Group': '', 'Google Shopping / MPN': '',
                       'Google Shopping / AdWords Grouping': '', 'Google Shopping / AdWords Labels': '',
                       'Google Shopping / Condition': '', 'Google Shopping / Custom Product': '',
                       'Google Shopping / Custom Label 0': '', 'Google Shopping / Custom Label 1': '',
                       'Google Shopping / Custom Label 2': '', 'Google Shopping / Custom Label 3': '',
                       'Google Shopping / Custom Label 4': '', 'Variant Image': '', 'Variant Weight Unit': '',
                       'Variant Tax Code': '', 'Cost per items': ''}
    new_line = {}

    option = 1

    template_header['Handle'] = handle
   
    if obj == 0 and img == 0:
        template_header['Title'] = title
        template_header['Body (HTML)'] = body
        template_header['Vendor'] = vendor
        template_header['Type'] = product_type

        tag_str = ''
        for tag in range(len(tags)):
            if tag == len(tags) - 1:
                tag_str += tags[tag]
            else:
                tag_str += tags[tag] + ', '
        template_header['Tags'] = tag_str
        template_header['Published'] = published
        template_header['Gift Card'] = gift_card

        for key, value in option_dicts[img].items():
            template_header['Option' + str(option) + ' Name'] = key
            template_header['Option' + str(option) + ' Value'] = value
            option += 1

        template_header['Variant SKU'] = skus[img]

        template_header['Variant Grams'] = total_weights[img]

        template_header['Variant Inventory Tracker'] = variant_inventory_tracker
        template_header['Variant Inventory Qty'] = int(float(quantity[obj]))
        template_header['Variant Inventory Policy'] = variant_inventory_policy
        template_header['Variant Fulfillment Service'] = variant_fulfillment_service
        template_header['Variant Price'] = price[0]
        template_header['Variant Compare At Price'] = price[1]
        template_header['Variant Requires Shipping'] = variant_requires_shipping
        template_header['Variant Taxable'] = variant_taxable

        template_header['Variant Barcode'] = barcodes[img]

        template_header['Variant Weight Unit'] = weight_unit
        template_header['Image Src'] = main_img[img]
        template_header['Image Position'] = img + 1
        template_header['Image Alt Text'] = alt_text[img]
        template_header['SEO Title'] = seo_title
        template_header['Cost per items'] = int(float(cost_per_item[obj]))


        new_line = template_header

    else:
        if obj >= 1 and img == 0:

            for key, value in option_dicts[obj].items():
                template_header['Option' + str(option) + ' Value'] = value
                option += 1

            template_header['Variant SKU'] = skus[obj]
            template_header['Variant Grams'] = total_weights[obj]
            template_header['Variant Inventory Tracker'] = variant_inventory_tracker
            template_header['Variant Inventory Qty'] = int(float(quantity[obj]))
            template_header['Variant Inventory Policy'] = variant_inventory_policy
            template_header['Variant Fulfillment Service'] = variant_fulfillment_service
            template_header['Variant Requires Shipping'] = variant_requires_shipping
            template_header['Variant Taxable'] = variant_taxable
            template_header['Variant Barcode'] = barcodes[obj]
            template_header['Variant Weight Unit'] = weight_unit

            template_header['Image Src'] = main_img[img]
            template_header['Image Position'] = img + 1
            template_header['Image Alt Text'] = alt_text[obj]
            template_header['Cost per items'] = int(float(cost_per_item[obj]))
            template_header['Variant Price'] = price[0]
            template_header['Variant Compare At Price'] = price[1]


            new_line = template_header
        else:
            try:
                template_header['Image Src'] = main_img[img]
            except IndexError:
                pass
            template_header['Image Position'] = img + 1
            if obj_num > 1:
                template_header['Image Alt Text'] = alt_text[obj]
            new_line = template_header

    return new_line

#! Change the range of products here
# PRODUCT WITH LETTERS FOR MODEL: decide whether product has varients
def classify_product_1(sorted_list):
    # print(len(sorted_list))
    model = sorted_list[0]['Model #'].strip()

    return_list = []
    group_list = []
    temp_prod = ''

    for product in sorted_list[0:]:

        p_model = product['Model #'].rsplit('-',1)[0].strip()

        # if left part of model of the product match with model
        if p_model == model.rsplit('-',1)[0]:

            # if it's the same product
            if product['Model #'].strip() == model:
                temp_prod = product
            
            elif product['Model #'].split('-',0)[0].strip() == model.split('-',0)[0].strip():
                group_list.append(temp_prod)
                temp_prod = product
            # if it's not the same product, but belongs to the same group
            else:
                group_list.append(temp_prod)
                temp_prod = product
        # if left part of model of the product doesn't match with model
        else:
            if not group_list:
                return_list.append([temp_prod])
                
            else:
                group_list.append(temp_prod)
                return_list.append(group_list)
                group_list = []
            model = product['Model #'].strip()
                
            temp_prod = product


    return return_list

#! Change the range of products here
# decide whether product has varients
def classify_product(sorted_list):
    model = sorted_list[0]['Model #'].strip()

    return_list = []
    group_list = []
    temp_prod = ''

    for product in sorted_list[0:]:

        p_model = product['Model #'].split('-')[0].strip()

        # if left part of model of the product match with model
        if p_model == model.split('-')[0]:

            # if it's the same product
            if product['Model #'].strip() == model:
                temp_prod = product
            # if it's not the same product, but belongs to the same group
            else:
                group_list.append(temp_prod)
                temp_prod = product
        # if left part of model of the product doesn't match with model
        else:
            if not group_list:
                return_list.append([temp_prod])
                
            else:
                group_list.append(temp_prod)
                return_list.append(group_list)
                group_list = []
            model = product['Model #'].strip()
                
            temp_prod = product


    return return_list

def main():
    filename_price = 'Price List -  Bestar - September 2020 - Canada.csv'
    filename_matt = 'Price List-Bestar-Matt-1.csv'
    # filename_matt = 'product_import_template (many var imgs).csv'
    inventory_file = 'bestar inventory listnextdate.csv'

    # Return a list of new product SKUs with needed information
    price_list = preprocess_file(filename_price, filename_matt)

    # sort list of dictionaries by 'Model #'
    sorted_list = sorted(price_list, key=lambda i: i['Model #'])

    # REMOVE
    # sorted_list_1 = []
    # for i in sorted_list:
    #     l = []
    #     l.append(i)
    #     sorted_list_1.append(l)

    # product variant
    classified_list = classify_product(sorted_list)

    inc = 0
    with open('generated_new_Bestar_import.csv', 'w', newline='', encoding='utf8') as outputfile:
        writer = csv.DictWriter(outputfile, fieldnames=columns)
        writer.writeheader()

        title_exist = ''
        handle = ''
        count = 1

        for items in classified_list:
        # for items in sorted_list_1:
            
            product_type = get_type(items)
            option_dicts = get_option_name_value(items)
            barcodes = get_upc(items)
            total_weights = get_weight(items)

            skus = get_sku(items)
            print(skus)
            
            cost_per_item = get_cost_per_item(items)
            price = get_price(items, filename_matt)

            quantity = get_quantity(items, inventory_file)
            
            body = get_body_html(items, product_type)
            # print(body)
            img_lists = get_image(items)       
            # print(img_lists)

            tags = gen_tags(items)
            # print(tags)
            title, handle = get_title_handle(items)

            # Deal with products with the same Title and handle
            if title_exist == '':
                title_exist = title
            else:
                if title_exist == title:
                    title += " - " + str(count)
                    handle += "-" + str(count)
                    count += 1
                else:
                    title_exist = title

            alt_text = get_img_alt_text(items)

            seo_title = get_seo_title(title)
            # print(seo_title)
            obj_num = len(items)

            for obj in range(len(img_lists)):
                for i in range(len(img_lists[obj])):
                    line = produce_template_line(seo_title, handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, quantity, cost_per_item, price[obj], img_lists[obj], alt_text, i , obj, obj_num)
                    writer.writerow(line)
            inc += 1
    print(inc)


if __name__ == '__main__':
    main()
