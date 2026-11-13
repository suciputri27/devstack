<?php
class OrderController {
    public function index(Request $request) {
        $rows = DB::select("SELECT * FROM orders WHERE status = '$status'");
        $q = Order::whereRaw('name = ' . $request->name)->orderBy($request->sort)->get();
        return Order::findOrFail($request->id);
    }
    public function store(Request $request) {
        Order::create($request->all());
        $hash = md5($password);
        $body = file_get_contents($request->url);
        $request->file('f')->move(public_path('uploads'), $request->file('f')->getClientOriginalName());
        exec('convert ' . $file);
    }
    public function safe(Request $request) {
        return Order::where('user_id', $request->user()->id)->whereKey($uuid)->firstOrFail();
    }
}
