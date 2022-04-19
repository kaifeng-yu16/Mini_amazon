#ifndef _SQL_FUNCTION_H
#define _SQL_FUNCTION_H

#include <fstream>
#include <iostream>
#include <pqxx/pqxx>
#include <string>
#include "exception.h"
#include "warehouse.h"

/*------------------Table Names-------------*/
#define PRODUCT "amazon_product"
#define INVENTORY "amazon_inventory"
#define CATEGORY "amazon_category"
#define ITEM "amazon_item"
#define ORDER "amazon_order"
#define WAREHOUSE "amazon_warehouse"

using namespace std;
using namespace pqxx;

void initFromDB();
bool checkInventory(int w_id, int p_id, int purchase_amount);
void readOrder(int o_id);

#endif