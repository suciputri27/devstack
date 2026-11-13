<?php
class Pesanan extends CI_Controller {
    public function cari() {
        $q = $this->db->query("SELECT * FROM pesanan WHERE kode = '" . $this->input->get('kode') . "'");
        $r = $this->db->where('id', $this->input->get('id'))->get('pesanan');
        echo $this->input->get('q');
        $ok = $this->db->query('SELECT * FROM pesanan WHERE kode = ?', [$kode]);
    }
}
