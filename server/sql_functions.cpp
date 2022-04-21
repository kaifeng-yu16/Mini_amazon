#include "sql_functions.h"
#include "server.h"
#include "warehouse.h"

/*
    1) read product from Database, store in Warehouse::productList
    2) read warehouse amount and locations from Database
    If any of them is initialized(db empty), throw Uninitialize exception
*/
void initFromDB() {
    cout << "Start to initfromDB.\n";
    Server& s = Server::get_instance();
    cout << "get_instance success.\n";
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success.\n";
    nontransaction N(*C.get());
    cout << "C.get success.\n";
    stringstream sql;
    cout << "Start to initfromDB.\n";
    // Initialize Server.productList
    sql << "SELECT p_id, name FROM " << PRODUCT << ";";
    result products(N.exec(sql.str()));
    if (products.empty()) {
        throw Uninitialize("No products in database.");
    }
    for (auto const& p : products) {
        int p_id = p[0].as<int>();
        string p_name = p[1].as<string>();
        Server::get_instance().productList.push_back(Product(p_id, p_name));
    }
    cout << "Initialized Product list.\n";
    // sql.clear();
    sql.str("");

    // Initialize Server.whlist
    sql << "SELECT w_id, loc_x, loc_y FROM " << WAREHOUSE << ";";
    result warehouses(N.exec(sql.str()));
    s.disConnectDB(C.get());
    if (warehouses.empty()) {
        throw Uninitialize("No warehouses in database.");
    }
    s.num_wh = warehouses.capacity();
    for (auto const& wh : warehouses) {
        int w_id = wh[0].as<int>();
        int loc_x = wh[1].as<int>();
        int loc_y = wh[2].as<int>();
        unique_ptr<Warehouse> warehouse(new Warehouse(w_id, loc_x, loc_y));
        s.whlist.push_back(move(warehouse));
    }
    cout << "Initialized Warehouse list.\n";
}

/*
    Check inventory in DB, if sufficient for order, reserve products
   simultaneously and return true return false if insufficient
*/
bool checkInventory(int w_id, int p_id, int purchase_amount) {
    Server& s = Server::get_instance();
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success in checkInventory.\n";
    work W(*C.get());
    stringstream sql;

    sql << "UPDATE " << INVENTORY << " SET count=" << INVENTORY << ".count-"
        << purchase_amount << " WHERE " << INVENTORY << ".product_id=" << p_id
        << " AND " << INVENTORY << ".warehouse_id=" << w_id << " AND "
        << INVENTORY << ".count>=" << purchase_amount << ";";
    result R;
    try {
        R = W.exec(sql.str());
        W.commit();
    } catch (const pqxx::pqxx_exception& e) {
        W.abort();
        std::cerr << "Database Error in check_inventory: " << e.base().what()
                  << std::endl;
    }
    s.disConnectDB(C.get());
    result::size_type rows = R.affected_rows();
    if (rows == 0) {
        return false;
    }
    return true;
}

/*
    Given an order id, read the order info from DB --> Separate to multiple
   items, then push them into the purchaseQueue
   Update warehouse num of each item in DB
   single thread: no synchronization issues
*/
void readOrder(int o_id) {
    Server& s = Server::get_instance();
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success in readOrder.\n";
    nontransaction N(*C.get());
    stringstream sql;

    sql << "SELECT i_id, p_id, name, count, loc_x, loc_y FROM " << ITEM << ", "
        << PRODUCT << ", " << ORDER << " WHERE " << ITEM << ".order_id=" << o_id
        << " AND " << ITEM << ".product_id=" << PRODUCT << "."
        << "p_id AND " << ORDER << ".o_id=" << o_id << ";";
    result order(N.exec(sql.str()));

    if (order.capacity() == 0) {
        throw MyException(
            "Order id does not exist in database or order dose not conatains "
            "any items.");
    }

    int wh_index = -1;

    for (auto const& item : order) {
        int i_id = item[0].as<int>();
        int p_id = item[1].as<int>();
        string name = item[2].as<string>();
        int purchase_amount = item[3].as<int>();
        int loc_x = item[4].as<int>();
        int loc_y = item[5].as<int>();

        // Select warehouse --> all the items in the same order are assigned to
        // the same wh
        if (wh_index == -1) {
            wh_index = selectWarehouse(loc_x, loc_y);
        }

        // Construct SubOrder Object
        shared_ptr<SubOrder> order(
            new SubOrder(i_id, p_id, name, purchase_amount, loc_x, loc_y));
        // Push in queue
        pushInQueue(wh_index, order);
    }

    int whnum = s.whlist[wh_index]->w_id;

    work W(*C.get());
    sql.clear();
    sql.str("");
    sql << "UPDATE " << ITEM << "," << WAREHOUSE << "," << ORDER << " SET "
        << ITEM << ".warehouse_id=" << whnum << " WHERE " << ITEM
        << ".order_id=" << o_id << ";";
    try {
        W.exec(sql.str());
        W.commit();
    } catch (const pqxx::pqxx_exception& e) {
        W.abort();
        std::cerr << "Database Error in read_order while updating whnum: "
                  << e.base().what() << std::endl;
    }
    s.disConnectDB(C.get());
}

// add inventory to specific warehouse
void add_inventory(int w_id, int p_id, int count) {
    Server& s = Server::get_instance();
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success in add_inventory.\n";
    work W(*C.get());
    stringstream sql;
    sql << "UPDATE " << INVENTORY << " SET count=" << INVENTORY << ".count+"
        << count << " WHERE " << INVENTORY << ".product_id=" << p_id << " AND "
        << INVENTORY << ".warehouse_id=" << w_id << ";";
    try {
        W.exec(sql.str());
        W.commit();
    } catch (const pqxx::pqxx_exception& e) {
        W.abort();
        std::cerr << "Database Error in add_inventory: " << e.base().what()
                  << std::endl;
    }
    s.disConnectDB(C.get());
}

// change order status to packed and return if ups truck has arrived
// throw if current order status is not open
tuple<bool, int, int> packed_and_check_ups_truck(int i_id) {
    Server& s = Server::get_instance();
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success in packed_and_check_ups_truck.\n";
    work W(*C.get());
    stringstream sql;
    sql << "UPDATE " << ITEM << " SET status='packed' WHERE " << ITEM
        << ".i_id=" << i_id
        << " AND status='new' RETURNING ups_truckid, warehouse_id;";
    result R;
    try {
        R = W.exec(sql.str());
        W.commit();
    } catch (const pqxx::pqxx_exception& e) {
        W.abort();
        std::cerr << "Database Error in packed_and_check_ups_truck: "
                  << e.base().what() << std::endl;
    }
    s.disConnectDB(C.get());
    if (R.begin() == R.end()) {
        throw MyException(
            "item id does not exist(unlikely) or status is not open.\n");
    }
    bool res = !(R.begin()[0].is_null());
    int truck_id = 0;
    int w_id;
    if (res == true) {
        truck_id = R.begin()[0].as<int>();
    }
    if (R.begin()[1].is_null()) {
        throw MyException("Do not have a valid warehouse id.\n");
    } else {
        w_id = R.begin()[1].as<int>();
    }
    return make_tuple(res, truck_id, w_id);
}

// change order status to delivering
// throw if current order status is not packed or do not have ups_truckid
void change_status_to_delivering(int i_id) {
    Server& s = Server::get_instance();
    unique_ptr<connection> C(s.connectDB());
    cout << "connectDB success in change_status_to_delivering.\n";
    work W(*C.get());
    stringstream sql;
    sql << "UPDATE " << ITEM
        << " SET status='delivering' WHAND status='packed' AND ups_truckid IS "
           "NOT NULERE "
        << ITEM << ".i_id=" << i_id
        << " AND status='packed' AND ups_truckid IS NOT NULL;";
    result R;
    try {
        R = W.exec(sql.str());
        W.commit();
    } catch (const pqxx::pqxx_exception& e) {
        W.abort();
        std::cerr << "Database Error in change_status_to_delivering: "
                  << e.base().what() << std::endl;
    }
    s.disConnectDB(C.get());
    if (R.begin() == R.end()) {
        throw MyException(
            "item id does not exist(unlikely) or status is not packed or do "
            "not have ups_truckid.\n");
    }
}
