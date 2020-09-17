import csv
import pandas as pd
import re

# * Use OOP for the next vendors

#! Structure:
# 1) Extract all the necessary information from the price list
# 2) Preprocess the information to match the template_column_name
# 3) Write to a file all the information

columns = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker', 'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping', 'Variant Taxable', 'Variant Barcode', 'Image Src', 'Image Position', 'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description',
           'Google Shopping / Google Product Category', 'Google Shopping / Gender', 'Google Shopping / Age Group', 'Google Shopping / MPN', 'Google Shopping / AdWords Grouping', 'Google Shopping / AdWords Labels', 'Google Shopping / Condition', 'Google Shopping / Custom Product', 'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1', 'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3', 'Google Shopping / Custom Label 4', 'Variant Image', 'Variant Weight Unit', 'Variant Tax Code', 'Cost per items']

info_fields = ['Model #', 'Image 1', 'Image 2', 'Image 3', 'Image 4', 'Image 5', 'Image 6', 'Image 7', 'Image 8', 'Image 9', 'Image 10', 'Image 11',
               'Image 12', 'Product Name', 'Features', 'Brand', 'Total Weight', 'Delivered Cost CA', 'Cost', 'UPC Code', 'Color', 'Category #1', 'Category #2']
           
vendor = 'Pending - Bestar'
published = 'FALSE'
variant_inventory_tracker = 'shopify'
variant_inventory_policy = 'deny'
variant_fulfillment_service = 'manual'
variant_taxable = 'TRUE'
variant_requires_shipping = 'TRUE'
gift_card = 'FALSE'
weight_unit = 'lb'
                       
#! Change the source file to have only new products
# Remove first line and preprocess second line to be the header for key/value pairs
# Return a list of new product SKUs with info: ['Model # ', 'Images[1-12]', 'Product Name', 'Features', 'Brand', 'Delivered Cost CA', 'Cost', 'Total Weight', '1', 'UPC Code']
def preprocess_file(file_p, file_s):

    p_dict = []
    new_skus = []
    price_list = []

    sku_file = pd.read_csv(file_s)

    # Append all SKUs from 'Bestar SKU GoWFB.ca list' to new_skus list
    for row in sku_file.to_dict('records'):
        for k, v in row.items():
            if k == 'SKU':
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

#! Change the range of products here
# decide whether product has varients
def classify_product(sorted_list):
    model = sorted_list[70]['Model #'].strip()

    return_list = []
    group_list = []
    temp_prod = ''

    for product in sorted_list[70:110]:
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
            temp_prod = product
            

    return return_list

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
                    handle = v.lower().replace(' ', '-').replace('---', '-')
                else:
                    continue

    if len(pl) > 1:
        mod_title = title.split('-')[0].strip()
        title = mod_title + ' - Available in ' + str(len(pl)) + ' Colours'
        handle = mod_title.lower().replace(' ', '-')
        
    return title, handle

# Generate Alt Img Text
def get_img_alt_text(items):
    
    img_alt_text = []

    for product in items:
        img_alt_text.append(product['Product Name'].replace('Bestar', '').strip())

   
    return img_alt_text

# Split and preprocess 'Features' text into tokens
# [-] splits two tokens written together
# [-] merges incomplete sentces into one
def get_text(product):

    text = ''
    complete_sentences = []
    for k, v in product.items():
        if k == 'Features':
            # print(v,'\n')
            text = v

    x = re.split(r'(([A-Za-z])[.!?)])', text)
  
    try:
        for sent in range(len(x)):
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
        pass

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
    # Add sentences from specifications to desciption and delete those from specifications
    try:
        for i in specifications:
            if warranty != '':
                description.append(i)           
            else:
                if "limited warranty." in i:
                    warranty = i
    except IndexError:
        pass

    # Remove dimensions sentences from specifications
    for s in specifications:
        index = specifications.index(s)
        q = s.count('”') 
        q1 = s.count('"') 
        
        if q > 2 or q1 > 2:
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
    
    specifications = [x for x in specifications if x not in description and x not in dimensions]
    
    # Strip white spaces between '.' and '"' in dimensions
    for d in dimensions:
        index = dimensions.index(d)
        dim = ''
        if 'Interior dimensions' in d:
            dim = d.split('are')[1].strip().replace(" ","").replace('x', ' x ')
            dimensions.remove(d)
            dimensions.insert(index, dim)
        elif ', commercial' in d:
            dim = d.split(', commercial')[0].strip().replace(" ","").replace('x', ' x ')
            dimensions.remove(d)
            dimensions.insert(index, dim)
        elif 'mattresses' in d or 'mattress' in d:
            pass

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
    structure = '<h4>Description</h4>\n' + '<p>Items Included</p>\n' + '<ul>\n' + '<li>...</li>\n' + '</ul>\n' + '<meta charset="utf-8">\n' + \
        '<p><span>...</span></p>\n' + '<h4>Dimensions</h4>\n' + '<p>...</p>\n' + \
        '<h4>Specifications</h4>\n' + '<ul>\n' + '<li>...</li>\n' + '</ul>'

    for product in pl:
        text = get_text(product)
        break

    description, specifications, dimensions = categorize_text(text)

    # Append sentences in DESCRIPTION list to body IF EXIST
    if description:
        desc = ''
        for row in description:
            desc += row

        body += '<h4>Description</h4>\n' + '<p>items Included</p>\n'
        body += '<ul>\n' + '<li>' + p_type + '</li>\n' + \
            '</ul>\n' + '<meta charset="utf-8">\n'
        body += '<p><span>' + desc + '</span></p>\n' + '<h4>Dimensions</h4>\n'
    else:
        pass

    # Append sentences in DIMENSIONS list to body IF EXIST
    if dimensions:
        for row in dimensions:
            body += '<p>' + row + ' ' + '</p>\n'

    body += '<h4>Specifications</h4>\n' + '<ul>\n'

    # Append sentences in SPECIFICATIONS list to body IF EXIST
    if specifications:
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

    product_tags = ['Bestar', 'Brand_Modubox', 'Made In_Canada']

    for product in pl:
        for k, v in product.items():
            if k == 'Color':
                if '&' in v:
                    tag1 = 'Colour_' + v.split('&')[0].strip()
                    tag2 = 'Colour_' + v.split('&')[1].strip()
                    if tag1 not in product_tags:
                        product_tags.append(tag1)
                    elif tag2 in product_tags:
                        product_tags.append(tag2)
                    else:
                        pass
                else:
                    tag1 = 'Colour_' + v.strip()
                    product_tags.append(tag1)
            elif k == 'Category #1':
                if v == 'Desks' and 'Type_Desk' not in product_tags:
                    product_tags.append('Type_Desk')
            elif k == 'Category #2':
                if v == 'Desk Sets' and 'Room_Home Office' not in product_tags:
                    product_tags.append('Room_Home Office')

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
                price = v.split('$')[1].strip()
                costs.append(price)
 
    return costs


def produce_template_line(handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, cost_per_item, main_img, alt_text, img, obj, obj_num):

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
        template_header['Variant Inventory Qty'] = 1
        template_header['Variant Inventory Policy'] = variant_inventory_policy
        template_header['Variant Fulfillment Service'] = variant_fulfillment_service
        template_header['Variant Price'] = '0.0'
        template_header['Variant Compare At Price'] = '0.0'
        template_header['Variant Requires Shipping'] = variant_requires_shipping
        template_header['Variant Taxable'] = variant_taxable

        template_header['Variant Barcode'] = barcodes[img]

        template_header['Variant Weight Unit'] = weight_unit
        template_header['Image Src'] = main_img[img]
        template_header['Image Position'] = img + 1
        template_header['Image Alt Text'] = alt_text[img]
        template_header['Cost per items'] = cost_per_item[obj]


        new_line = template_header

    else:
        if obj >= 1 and img == 0:

            for key, value in option_dicts[obj].items():
                template_header['Option' + str(option) + ' Value'] = value
                option += 1

            template_header['Variant SKU'] = skus[obj]
            template_header['Variant Grams'] = total_weights[obj]
            template_header['Variant Inventory Tracker'] = variant_inventory_tracker
            template_header['Variant Inventory Qty'] = 1
            template_header['Variant Inventory Policy'] = variant_inventory_policy
            template_header['Variant Fulfillment Service'] = variant_fulfillment_service
            template_header['Variant Price'] = '0.0'
            template_header['Variant Compare At Price'] = '0.0'
            template_header['Variant Requires Shipping'] = variant_requires_shipping
            template_header['Variant Taxable'] = variant_taxable
            template_header['Variant Barcode'] = barcodes[obj]
            template_header['Variant Weight Unit'] = weight_unit
            template_header['Image Src'] = main_img[obj]
            template_header['Image Position'] = img + 1
            template_header['Image Alt Text'] = alt_text[obj]
            template_header['Cost per items'] = cost_per_item[obj]


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


def main():
    filename_price = 'Price List -  Bestar - September 2020 - Canada.csv'
    filename_sku = 'Bestar SKU GoWFB.ca list.csv' # - change file to Matt's pricelist
    filename_template = 'product_export_template.csv'

    # Return a list of new product SKUs with needed information
    price_list = preprocess_file(filename_price, filename_sku)

    # sort list of dictionaries by 'Model #'
    sorted_list = sorted(price_list, key=lambda i: i['Model #'])

    classified_list = classify_product(sorted_list)
    
    # for product in classified_list:
    #     # if product[0]['Model #'] == '109220-000017':
    #     skus = get_sku(product)
    #     print(skus)
    #     text = get_text(product[0])

    #     description, specifications, dimensions = categorize_text(text)

    #     print('Specifications: ' , specifications)
    #     print("\nDescription: " , description)
    #     print('\nDimensions: ' , dimensions , '\n')

    with open('generated_new_Bestar_import.csv', 'w', newline='') as outputfile:
        writer = csv.DictWriter(outputfile, fieldnames=columns)
        writer.writeheader()

        for items in classified_list:

            product_type = get_type(items)
            option_dicts = get_option_name_value(items)
            barcodes = get_upc(items)
            total_weights = get_weight(items)

            skus = get_sku(items)
            # print(skus)
            cost_per_item = get_cost_per_item(items)
            
            body = get_body_html(items, product_type)
            img_lists = get_image(items)       

            tags = gen_tags(items)
            title, handle = get_title_handle(items)
            
            alt_text = get_img_alt_text(items)
            obj_num = len(items)

            for obj in range(len(img_lists)):
                for i in range(len(img_lists[obj])):
                    line = produce_template_line(handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, cost_per_item, img_lists[obj], alt_text, i , obj, obj_num)
                    writer.writerow(line)


if __name__ == '__main__':
    main()

