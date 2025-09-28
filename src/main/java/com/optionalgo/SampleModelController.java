package com.optionalgo;

import com.optionalgo.model.SampleModel;
import com.optionalgo.repository.SampleModelRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/sample")
public class SampleModelController {
    @Autowired
    private SampleModelRepository repository;

    @GetMapping
    public List<SampleModel> getAll() {
        return repository.findAll();
    }

    @PostMapping
    public SampleModel add(@RequestBody SampleModel model) {
        return repository.save(model);
    }
}
