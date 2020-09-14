import csv
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import itertools
import collections
from itertools import groupby

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
                       
# Working with CSV file extention.
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

#? Change the range of products here
# decide whether product has varients
def classify_product(sorted_list):
    model = sorted_list[35]['Model #'].strip()

    return_list = []
    group_list = []
    temp_prod = ''

    for product in sorted_list[35:42]:
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
            model = product['Model #'].strip()
            

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
        count += 1
        for k, v in product.items():
            if k == 'Product Name':
                title = v
                if handle == '':
                    handle = v.lower().replace(' ', '-').replace('---', '-')
                else:
                    continue
        # handles.append(handle)

    if count > 1:
        mod_title = title.split('-')[0].strip()
        title = mod_title + ' - Available in ' + str(count) + ' Colours'

    return title, handle

# Find longest img list out of main_img list and var_img list
def longest_list(lst): 
    maxList = max(lst, key = lambda i: len(i)) 
    return maxList

#! Not ready and not used
def get_img_alt_text(vendor, title, items, img_lists):
    
    alt_text = ''
    color = ''
    img_alt_text = []
    # main_img = img_lists[0]
    # var_img = img_lists[1]

    long_lst = long_lst(img_lists)

    for product in items:
        for k,v in product.items():
            if k == 'Color':
                color = v


    for i in long_lst:
        if '&' in title:
            alt_text = vendor + ' ' + title
        else:
            alt_text = vendor + ' ' + color + ' ' + title

        img_alt_text.append(alt_text)

    return img_alt_text

# Split and preprocess 'Features' text into tokens
# [-] splits two tokens written together
# [-] merges incomplete sentces into one
def get_text(product):

    end_chars = ['.', '?', '!']
    tokens = []
    complete_sentences = []

    for k, v in product.items():
        if k == 'Features':
            for char in end_chars:
                if char in v:
                    test = v.split(char)

                    for i in test:
                        sent = ''
                        sent = i.strip() + char
                        tokens.append(sent)
            break

    
    # print('TOKENS: ',tokens , '\n')
    # merge incomplete tokens into one and add the complete tokens to complete_sentences list
    try:
        for i in range(len(tokens)):
            string = ''
            if '”' in tokens[i] or '"' in tokens[i]:
                continue
            elif '”' in tokens[i + 1] or '"' in tokens[i + 1]:
                if'”' in tokens[i + 2] or '"' in tokens[i + 2]:
                    string = tokens[i] + ' ' + tokens[i + 1] + ' ' + tokens[i + 2]
                    complete_sentences.append(string)
                elif '”' in tokens[i + 3] or '"' in tokens[i + 3]:
                    string = tokens[i] + ' ' + tokens[i + 1] + ' ' + tokens[i + 2] + ' ' + tokens[i + 3]
                    complete_sentences.append(string)
                else:
                    string = tokens[i] + ' ' + tokens[i + 1]
                    complete_sentences.append(string)
            else:
                complete_sentences.append(tokens[i])
            
    except IndexError:
        pass

    # print(complete_sentences)
    return complete_sentences

# Categorize sentences into desription, specifications, dimensions
# ? re for dimention extraction: '\d.*[A-Z]'
def categorize_text(text):
    description = []
    specifications = []
    dimensions = []

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
            elif first == 'Dimensions' or first == 'Interior':
                dim_sent += sent + ' '
                dimensions.append(dim_sent)
            else:
                if spec_sent != '' and dim_sent == '':
                    specifications.append(sent + ' ')
                elif spec_sent != '' and dim_sent != '':
                    dimensions.append(sent + ' ')
                else:
                    description.append(sent + ' ')
    except IndexError:
        pass
    # print("Description: " , description)
    # print('\nSpecifications: ' , specifications)
    # print('\nDimensions: ' , dimensions)

    return description, specifications, dimensions

# Produce text in HTML format
def get_body_html(pl, p_type):

    body = ''
    structure = '<h4>Description</h4>\n' + '<p>items Included</p>\n' + '<ul>\n' + '<li>...</li>\n' + '</ul>\n' + '<meta charset="utf-8">\n' + \
        '<p><span>...</span></p>\n' + '<h4>Dimensions</h4>\n' + '<p>...</p>\n' + \
        '<h4>Specifications</h4>\n' + '<ul>\n' + '<li>...</li>\n' + '</ul>'

    for product in pl:
        text = get_text(product)
        break

    description, specifications, dimensions = categorize_text(text)

    desc = ''
    for row in description:
        desc += row

    body += '<h4>Description</h4>\n' + '<p>items Included</p>\n'
    body += '<ul>\n' + '<li>' + p_type + '</li>\n' + \
        '</ul>\n' + '<meta charset="utf-8">\n'
    body += '<p><span>' + desc + '</span></p>\n' + '<h4>Dimensions</h4>\n'

    for row in dimensions:
        body += '<p>' + row + '</p>\n'

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
        else:
            sent += row

    body += '<li>' + sent + '</li>\n' + '</ul>'

    return body

# Get tags of each product and append it to listw
#! Need more tags
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
    main_img = []
    var_img = []
    count = 0
       
    for i in range(len(pl)):
        if len(pl) == 1:
            for k,v in pl[i].items():
                if 'Image' in k:
                    if str(v) == 'nan':
                        continue
                    else:
                        main_img.append(v)
            img_lists.append(main_img)
            img_lists.append([''])
        else:
            if i == 0:
                for k,v in pl[i].items():
                    if 'Image' in k:
                        if str(v) == 'nan':
                            continue
                        else:
                            main_img.append(v)
                img_lists.append(main_img)
                
            else:
                for k,v in pl[i].items():
                    if 'Image' in k:
                        if str(v) == 'nan':
                            continue
                        else:
                            var_img.append(v)
                img_lists.append(var_img)

    # print(img_lists)
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

#! Not finished
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

def produce_template_line(handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, main_img, var_img, img, obj_num):

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

    # ? if first dict is bigger, then over second iteration graps value 'Full' as oppose to only 'Black Grey & White'
    # option_dicts = [{'Colour': 'White & Rustic Brown'}, 'Size': 'Full'},
    #                 {'Colour': 'Black Grey & White'}]

    option = 1

    template_header['Handle'] = handle
    # template_header['Image Alt Text'] = ''
    
    if img == 0 :
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
        template_header['Variant Image'] = var_img[img]
        template_header['Image Position'] = img + 1

        new_line = template_header

    else:
        new_img = img + 1
        if new_img <= obj_num:

            # template_header['Title'] = title

            for key, value in option_dicts[img].items():
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
            template_header['Variant Image'] = var_img[img]
            template_header['Image Position'] = img + 1

            new_line = template_header
        else:
            if obj_num > 1:
                template_header['Variant Inventory Policy'] = variant_inventory_policy
                template_header['Variant Fulfillment Service'] = variant_fulfillment_service
            else:
                pass
            try:
                template_header['Image Src'] = main_img[img]
                template_header['Variant Image'] = var_img[img]
            except IndexError:
                pass
            template_header['Image Position'] = img + 1

            new_line = template_header


    
    return new_line


def main():
    filename_price = 'Price List -  Bestar - September 2020 - Canada.csv'
    filename_sku = 'Bestar SKU GoWFB.ca list.csv'
    filename_template = 'product_export_template.csv'

    # Return a list of new product SKUs with needed information
    price_list = preprocess_file(filename_price, filename_sku)

    # sort list of dictionaries by 'Model #'
    sorted_list = sorted(price_list, key=lambda i: i['Model #'])

    classified_list = classify_product(sorted_list)

    with open('new_bestar_list.csv', 'w', newline='') as outputfile:
        writer = csv.DictWriter(outputfile, fieldnames=columns)
        writer.writeheader()

        for items in classified_list:

            product_type = get_type(items)
            body = get_body_html(items, product_type)
            option_dicts = get_option_name_value(items)
            barcodes = get_upc(items)
            total_weights = get_weight(items)
            skus = get_sku(items)
            
            img_lists = get_image(items)       

            tags = gen_tags(items)
            title, handle = get_title_handle(items)
            
            obj_num = len(items)

            main_img = img_lists[0]
            var_img = img_lists[1]
            count = 0

            # run the loop until main product img list is exhausted
            for (i, v) in itertools.zip_longest(main_img, var_img, fillvalue=''):
                line = produce_template_line(handle, skus, barcodes, title, body, option_dicts, product_type, tags, total_weights, main_img, var_img, count , obj_num)
                writer.writerow(line)
                count += 1
            

if __name__ == '__main__':
    main()
